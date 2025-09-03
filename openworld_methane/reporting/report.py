from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from dataclasses import asdict
from datetime import timezone
from typing import Any, TextIO

from ..models import Anomaly, EmissionRecord, Remediation, WindowAggregate


def records_summary(records: Iterable[EmissionRecord]) -> dict[str, Any]:
    vals = [r.emission_rate_kg_per_h for r in records]
    if not vals:
        return {"count": 0, "mean": 0.0, "min": 0.0, "max": 0.0}
    return {
        "count": len(vals),
        "mean": sum(vals) / len(vals),
        "min": min(vals),
        "max": max(vals),
    }


def write_json_report(
    fp: TextIO,
    *,
    records: list[EmissionRecord] | None = None,
    anomalies: list[Anomaly] | None = None,
    aggregates: list[WindowAggregate] | None = None,
    remediations: list[Remediation] | None = None,
) -> None:
    payload: dict[str, Any] = {}
    if records is not None:
        payload["records"] = [
            {
                **asdict(r),
                "timestamp": r.timestamp.astimezone(timezone.utc).isoformat(),
            }
            for r in records
        ]
        payload["records_summary"] = records_summary(records)
    if anomalies is not None:
        payload["anomalies"] = [
            {
                **asdict(a),
                "record": {
                    **asdict(a.record),
                    "timestamp": a.record.timestamp.astimezone(timezone.utc).isoformat(),
                },
            }
            for a in anomalies
        ]
    if aggregates is not None:
        payload["aggregates"] = [
            {
                **asdict(agg),
                "start": agg.start.astimezone(timezone.utc).isoformat(),
                "end": agg.end.astimezone(timezone.utc).isoformat(),
            }
            for agg in aggregates
        ]
    if remediations is not None:
        payload["remediations"] = [
            {
                **asdict(r),
                "detected_at": r.detected_at.astimezone(timezone.utc).isoformat(),
                "due_by": r.due_by.astimezone(timezone.utc).isoformat(),
            }
            for r in remediations
        ]
    json.dump(payload, fp, indent=2, sort_keys=True)


def write_csv_aggregates(fp: TextIO, aggregates: Iterable[WindowAggregate]) -> None:
    fieldnames = [
        "start",
        "end",
        "site_id",
        "region_id",
        "count",
        "mean_kg_per_h",
        "min_kg_per_h",
        "max_kg_per_h",
        "sum_kg",
    ]
    writer = csv.DictWriter(fp, fieldnames=fieldnames)
    writer.writeheader()
    for agg in aggregates:
        writer.writerow(
            {
                "start": agg.start.astimezone(timezone.utc).isoformat(),
                "end": agg.end.astimezone(timezone.utc).isoformat(),
                "site_id": agg.site_id,
                "region_id": agg.region_id,
                "count": agg.count,
                "mean_kg_per_h": f"{agg.mean_kg_per_h:.6f}",
                "min_kg_per_h": f"{agg.min_kg_per_h:.6f}",
                "max_kg_per_h": f"{agg.max_kg_per_h:.6f}",
                "sum_kg": f"{agg.sum_kg:.6f}",
            }
        )
