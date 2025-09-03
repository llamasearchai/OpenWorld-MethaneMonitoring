from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict
from datetime import timezone
from typing import Any, TextIO

from ..core.timeutil import parse_timestamp
from ..core.units import to_kg_per_h
from ..models import EmissionRecord


def read_json(fp: TextIO) -> list[EmissionRecord]:
    data = json.load(fp)
    if not isinstance(data, list):
        raise ValueError("JSON must be a list of records")
    records: list[EmissionRecord] = []
    for row in data:
        try:
            ts = parse_timestamp(str(row["timestamp"]))
            site_id = str(row["site_id"])
            region_id = str(row["region_id"])
            value = float(row["value"])
            unit = str(row["unit"])
        except KeyError as e:
            raise ValueError(f"Missing key in JSON record: {e}") from e
        value_kg_h = to_kg_per_h(value, unit)  # type: ignore[arg-type]
        rec = EmissionRecord(
            timestamp=ts,
            site_id=site_id,
            region_id=region_id,
            emission_rate_kg_per_h=value_kg_h,
            source="json",
            meta={
                k: v
                for k, v in row.items()
                if k not in {"timestamp", "site_id", "region_id", "value", "unit"}
            },
        )
        records.append(rec)
    return records


def to_dicts(records: Iterable[EmissionRecord]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in records:
        d = asdict(r)
        d["timestamp"] = r.timestamp.astimezone(timezone.utc).isoformat()
        out.append(d)
    return out
