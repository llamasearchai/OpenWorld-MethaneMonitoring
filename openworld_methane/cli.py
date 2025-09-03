from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .alerts import EmailAlerter, SlackWebhookAlerter
from .analytics.aggregate import aggregate
from .analytics.anomaly import detect_anomalies, detect_anomalies_seasonal
from .compliance.rules import ThresholdRule, evaluate_threshold_rule
from .config import get_settings
from .core.logging import get_logger, setup_logging
from .dashboards.api import build_app
from .dashboards.ascii import render_dashboard
from .dashboards.http import serve_http
from .data_adapters.csv_adapter import read_csv as read_csv_records
from .data_adapters.json_adapter import read_json as read_json_records
from .models import EmissionRecord
from .persistence.indexed_jsonl import IndexedJsonlStore
from .persistence.jsonl import append_file as jsonl_append
from .persistence.jsonl import read_file as jsonl_read
from .persistence.store import DataStore
from .reporting.report import write_csv_aggregates, write_json_report


def _load_records_from_path(path: Path) -> list[EmissionRecord]:
    """Load records from a file path with error handling and logging."""
    logger = get_logger("cli")
    suffix = path.suffix.lower()

    if not path.exists():
        logger.error(f"File not found: {path}")
        raise SystemExit(f"File not found: {path}")

    if suffix not in {".csv", ".json"}:
        logger.error(f"Unsupported file type: {suffix}")
        raise SystemExit(f"Unsupported file type: {suffix}. Supported: .csv, .json")

    try:
        with path.open("r", encoding="utf-8") as fp:
            if suffix == ".csv":
                records = read_csv_records(fp)
            else:  # .json
                records = read_json_records(fp)

        logger.info(f"Loaded {len(records)} records from {path}")
        return records

    except Exception as e:
        logger.error(f"Failed to load records from {path}: {e}")
        raise SystemExit(f"Failed to load records from {path}: {e}")


def cmd_simulate(args: argparse.Namespace) -> int:
    import random

    now = datetime.now(tz=timezone.utc)
    rows = []
    for i in range(args.rows):
        ts = now - timedelta(minutes=(args.rows - i))
        site_id = f"site-{(i % args.sites) + 1}"
        region_id = f"region-{(i % args.regions) + 1}"
        base = 5.0 + (i % 7) * 0.2
        noise = random.uniform(-0.5, 0.5)
        spike = 8.0 if random.random() < args.spike_prob else 0.0
        val = max(0.0, base + noise + spike)
        rows.append(
            {
                "timestamp": ts.isoformat(),
                "site_id": site_id,
                "region_id": region_id,
                "value": round(val, 3),
                "unit": "kg/h",
            }
        )
    payload = rows
    if args.output.suffix.lower() == ".json":
        args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    else:
        import csv

        with args.output.open("w", encoding="utf-8", newline="") as fp:
            writer = csv.DictWriter(
                fp, fieldnames=["timestamp", "site_id", "region_id", "value", "unit"]
            )
            writer.writeheader()
            writer.writerows(payload)
    print(f"Wrote {len(rows)} simulated rows to {args.output}")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    in_path = Path(args.input)
    records = _load_records_from_path(in_path)
    # Normalize to dict
    dicts = [
        {
            **asdict(r),
            "timestamp": r.timestamp.astimezone(timezone.utc).isoformat(),
        }
        for r in records
    ]
    if args.output:
        Path(args.output).write_text(json.dumps(dicts, indent=2), encoding="utf-8")
        print(f"Wrote normalized JSON to {args.output}")
    else:
        json.dump(dicts, sys.stdout, indent=2)
        print()
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    path = Path(args.input)
    records = _load_records_from_path(path)
    if getattr(args, "method", "robust_z") == "robust_z":
        anomalies = detect_anomalies(records, z_threshold=args.z)
    else:
        anomalies = detect_anomalies_seasonal(records, period=args.period, z_threshold=args.z)
    report = [
        {
            "record": {
                **asdict(a.record),
                "timestamp": a.record.timestamp.astimezone(timezone.utc).isoformat(),
            },
            "score": a.score,
            "method": a.method,
            "threshold": a.threshold,
        }
        for a in anomalies
    ]
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Wrote anomalies JSON to {args.output}")
    else:
        json.dump(report, sys.stdout, indent=2)
        print()
    return 0


def cmd_aggregate(args: argparse.Namespace) -> int:
    path = Path(args.input)
    out = Path(args.output) if args.output else None
    records = _load_records_from_path(path)
    aggs = aggregate(records, args.window)
    if out and out.suffix.lower() == ".csv":
        with out.open("w", encoding="utf-8", newline="") as fp:
            write_csv_aggregates(fp, aggs)
        print(f"Wrote aggregates CSV to {out}")
    else:
        write_json_report(sys.stdout, aggregates=aggs)
        print()
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    path = Path(args.input)
    records = _load_records_from_path(path)
    anomalies = detect_anomalies(records, z_threshold=args.z)
    rule = ThresholdRule(rule_id="T1", threshold_kg_per_h=args.threshold, due_days=args.due_days)
    remediations = evaluate_threshold_rule(records, rule)
    out = Path(args.output) if args.output else None
    if out:
        with out.open("w", encoding="utf-8") as fp:
            write_json_report(fp, records=records, anomalies=anomalies, remediations=remediations)
        print(f"Wrote report to {out}")
    else:
        write_json_report(
            sys.stdout, records=records, anomalies=anomalies, remediations=remediations
        )
        print()
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    path = Path(args.input)
    records = _load_records_from_path(path)
    print(render_dashboard(records))
    return 0


def _load_into_store(store: DataStore, path: Path) -> int:
    records = _load_records_from_path(path)
    return store.append(records)


def _init_store_from_config(config_path: str | None) -> DataStore:
    """Initialize storage backend from configuration with improved performance."""
    cfg = get_settings(config_path)
    backend = cfg.storage.backend
    logger = get_logger("cli.storage")

    if backend == "jsonl":
        jsonl_path = cfg.storage.jsonl_path
        if not jsonl_path:
            raise SystemExit("storage.backend=jsonl requires storage.jsonl_path in config")

        path = Path(jsonl_path)
        logger.info(f"Using indexed JSONL store: {path}")
        return IndexedJsonlStore(path)  # type: ignore[return-value]

    logger.info(f"Using in-memory store (backend: {backend})")
    return DataStore()


def cmd_watch(args: argparse.Namespace) -> int:
    import time

    path = Path(args.input)
    store = _init_store_from_config(getattr(args, "config", None))
    last_mtime = 0.0
    # Initial load
    _load_into_store(store, path)
    print(f"Loaded {store.summary()['count']} records from {path}")
    while True:
        try:
            mtime = path.stat().st_mtime
        except FileNotFoundError:
            time.sleep(args.interval)
            continue
        if mtime > last_mtime:
            # reload
            store = _init_store_from_config(getattr(args, "config", None))
            _load_into_store(store, path)
            print(f"Reloaded: {store.summary()['count']} records")
            last_mtime = mtime
        time.sleep(args.interval)
    # unreachable
    # return 0


def cmd_serve(args: argparse.Namespace) -> int:
    path = Path(args.input)
    store = _init_store_from_config(getattr(args, "config", None))
    _load_into_store(store, path)
    serve_http(store, host=args.host, port=args.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="owm", description="OpenWorld Methane Monitoring CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("simulate", help="Generate synthetic dataset (CSV or JSON)")
    ps.add_argument("output", type=Path, help="Output file path (.csv or .json)")
    ps.add_argument("--rows", type=int, default=200)
    ps.add_argument("--sites", type=int, default=3)
    ps.add_argument("--regions", type=int, default=2)
    ps.add_argument("--spike-prob", type=float, default=0.05)
    ps.set_defaults(func=cmd_simulate)

    pi = sub.add_parser("ingest", help="Ingest file and normalize to JSON")
    pi.add_argument("input", help="Input file (.csv or .json)")
    pi.add_argument("--output", help="Output JSON file (default stdout)")
    pi.set_defaults(func=cmd_ingest)

    pa = sub.add_parser("analyze", help="Detect anomalies (robust Z or seasonal)")
    pa.add_argument("input", help="Input file (.csv or .json)")
    pa.add_argument("--method", choices=["robust_z", "seasonal"], default="robust_z")
    pa.add_argument("--period", type=int, default=24, help="Seasonal period")
    pa.add_argument("--z", type=float, default=3.5, help="Z-score threshold")
    pa.add_argument("--output", help="Output JSON file (default stdout)")
    pa.set_defaults(func=cmd_analyze)

    pg = sub.add_parser("aggregate", help="Aggregate by time window")
    pg.add_argument("input", help="Input file (.csv or .json)")
    pg.add_argument("--window", default="1h", help="Window like 1h, 15m, 30s")
    pg.add_argument("--output", help="Output file (.csv for CSV, otherwise JSON to stdout)")
    pg.set_defaults(func=cmd_aggregate)

    pr = sub.add_parser("report", help="Generate combined JSON report")
    pr.add_argument("input", help="Input file (.csv or .json)")
    pr.add_argument("--z", type=float, default=3.5, help="Z-score threshold")
    pr.add_argument("--threshold", type=float, default=10.0, help="Compliance threshold kg/h")
    pr.add_argument("--due-days", type=int, default=7, help="Remediation due days")
    pr.add_argument("--output", help="Output JSON file (default stdout)")
    pr.set_defaults(func=cmd_report)

    pd = sub.add_parser("dashboard", help="Render ASCII dashboard from data")
    pd.add_argument("input", help="Input file (.csv or .json)")
    pd.set_defaults(func=cmd_dashboard)

    pw = sub.add_parser("watch", help="Watch a file and reload on changes (poll)")
    pw.add_argument("input", help="Input file (.csv or .json)")
    pw.add_argument("--interval", type=int, default=5)
    pw.add_argument("--config", help="Path to TOML config file for storage backend")
    pw.set_defaults(func=cmd_watch)

    psrv = sub.add_parser("serve", help="Run simple HTTP dashboard server")
    psrv.add_argument("input", help="Input file (.csv or .json)")
    psrv.add_argument("--host", default="127.0.0.1")
    psrv.add_argument("--port", type=int, default=8000)
    psrv.add_argument("--config", help="Path to TOML config file for storage backend")
    psrv.set_defaults(func=cmd_serve)

    papi = sub.add_parser("api", help="Run FastAPI server (optional)")
    papi.add_argument("input", help="Input file (.csv or .json)")
    papi.add_argument("--host", default="127.0.0.1")
    papi.add_argument("--port", type=int, default=8000)
    papi.add_argument("--config", help="Path to TOML config file for storage backend")
    papi.set_defaults(func=cmd_api)

    pcfg = sub.add_parser("config", help="Load and validate configuration")
    pcfg.add_argument("--file", dest="file", help="Path to TOML config file")
    pcfg.set_defaults(func=cmd_config)

    pq = sub.add_parser("query", help="Query JSONL store with optional time range")
    pq.add_argument("path", help="Path to JSONL file")
    pq.add_argument("--start", help="Start ISO timestamp (inclusive)")
    pq.add_argument("--end", help="End ISO timestamp (exclusive)")
    pq.set_defaults(func=cmd_query)

    pn = sub.add_parser("notify", help="Send alerts to Slack and/or Email based on anomalies")
    pn.add_argument("input", help="Input file (.csv or .json)")
    pn.add_argument("--method", choices=["robust_z", "seasonal"], default="robust_z")
    pn.add_argument("--period", type=int, default=24)
    pn.add_argument("--z", type=float, default=3.5)
    pn.add_argument("--dry-run", action="store_true")
    # Slack
    pn.add_argument("--slack-webhook-url")
    # Email SMTP
    pn.add_argument("--smtp-host")
    pn.add_argument("--smtp-port", type=int, default=25)
    pn.add_argument("--smtp-user")
    pn.add_argument("--smtp-pass")
    pn.add_argument("--smtp-tls", action="store_true")
    pn.add_argument("--email-from")
    pn.add_argument("--email-to", help="Comma-separated recipients")
    pn.set_defaults(func=cmd_notify)

    plog = sub.add_parser("log", help="Append normalized records to a JSONL log file")
    plog.add_argument("input", help="Input file (.csv or .json)")
    plog.add_argument("output", type=Path, help="Output JSONL file path")
    plog.set_defaults(func=cmd_log)

    return p


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point with logging setup."""
    try:
        # Initialize basic logging first
        setup_logging()
        logger = get_logger("cli")

        parser = build_parser()
        args = parser.parse_args(argv)

        # Set up application-level logging based on config if available
        config_path = getattr(args, 'config', None)
        if config_path:
            try:
                cfg = get_settings(config_path)
                setup_logging(cfg.logging)
                logger = get_logger("cli")  # Refresh logger with new config
            except Exception as e:
                logger.warning(f"Failed to load logging config from {config_path}: {e}")

        logger.info(f"Starting command: {args.cmd}")
        result = args.func(args)
        logger.info(f"Command completed successfully: {args.cmd}")
        return result

    except KeyboardInterrupt:
        logger = get_logger("cli")
        logger.info("Operation cancelled by user")
        return 130  # Standard exit code for Ctrl+C

    except SystemExit as e:
        logger = get_logger("cli")
        logger.error(f"System exit: {e}")
        raise

    except Exception as e:
        logger = get_logger("cli")
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


def cmd_notify(args: argparse.Namespace) -> int:
    path = Path(args.input)
    records = _load_records_from_path(path)
    if args.method == "robust_z":
        anomalies = detect_anomalies(records, z_threshold=args.z)
    else:
        anomalies = detect_anomalies_seasonal(records, period=args.period, z_threshold=args.z)
    total = 0
    dispatched = False
    if args.slack_webhook_url:
        dispatched = True
        slack = SlackWebhookAlerter(webhook_url=args.slack_webhook_url, dry_run=args.dry_run)
        total += slack.send_anomalies(anomalies)
    if args.smtp_host and args.email_to and args.email_from:
        dispatched = True
        email = EmailAlerter(
            smtp_host=args.smtp_host,
            smtp_port=args.smtp_port,
            username=args.smtp_user,
            password=args.smtp_pass,
            use_tls=args.smtp_tls,
            sender=args.email_from,
            recipients=[e.strip() for e in args.email_to.split(",") if e.strip()],
            dry_run=args.dry_run,
        )
        total += email.send_anomalies(anomalies)
    if not dispatched:
        print(
            "No alert channel configured; use --slack-webhook-url or SMTP + --email-to/--email-from."
        )
    print(
        f"Processed {len(anomalies)} anomalies; dispatched {total} notifications (dry_run={args.dry_run})."
    )
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    path = Path(args.input)
    out = Path(args.output)
    records = _load_records_from_path(path)
    n = jsonl_append(out, records)
    print(f"Appended {n} records to {out}")
    return 0


def cmd_config(args: argparse.Namespace) -> int:
    cfg = get_settings(args.file)
    # Render as JSON via Pydantic
    import json as _json

    print(_json.dumps(cfg.model_dump(), indent=2, sort_keys=True))
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    from .core.timeutil import parse_timestamp

    path = Path(args.path)
    recs = jsonl_read(path)
    start = parse_timestamp(args.start) if args.start else None
    end = parse_timestamp(args.end) if args.end else None
    if start or end:

        def in_range(r: EmissionRecord) -> bool:
            if start and r.timestamp < start:
                return False
            if end and r.timestamp >= end:
                return False
            return True

        recs = [r for r in recs if in_range(r)]
    write_json_report(sys.stdout, records=recs)
    print()
    return 0


def cmd_api(args: argparse.Namespace) -> int:
    # Lazy import; avoid a hard dependency if not used
    try:
        import uvicorn  # type: ignore
    except Exception as err:  # noqa: BLE001
        raise SystemExit(
            "uvicorn is required for 'api' command; install extras: pip install uvicorn fastapi"
        ) from err

    path = Path(args.input)
    store = _init_store_from_config(getattr(args, "config", None))
    _load_into_store(store, path)
    app = build_app(store)
    uvicorn.run(app, host=args.host, port=args.port)
    return 0
