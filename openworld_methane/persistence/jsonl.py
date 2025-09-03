from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO, cast

from ..models import EmissionRecord
from .store import Store


def write_records(fp: TextIO, records: Iterable[EmissionRecord]) -> int:
    n = 0
    for r in records:
        obj = {
            "timestamp": r.timestamp.astimezone(timezone.utc).isoformat(),
            "site_id": r.site_id,
            "region_id": r.region_id,
            "emission_rate_kg_per_h": r.emission_rate_kg_per_h,
        }
        fp.write(json.dumps(obj) + "\n")
        n += 1
    return n


def read_records(fp: TextIO) -> list[EmissionRecord]:
    records: list[EmissionRecord] = []
    for line in fp:
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        # Compatible read if value/unit provided instead of normalized
        if "emission_rate_kg_per_h" in obj:
            from ..core.timeutil import parse_timestamp

            ts = parse_timestamp(obj["timestamp"])  # normalize tz
            records.append(
                EmissionRecord(
                    timestamp=ts,
                    site_id=str(obj["site_id"]),
                    region_id=str(obj["region_id"]),
                    emission_rate_kg_per_h=float(obj["emission_rate_kg_per_h"]),
                    source="jsonl",
                )
            )
        else:
            # fallback to full conversion path
            from ..core.timeutil import parse_timestamp
            from ..core.units import Unit, to_kg_per_h

            ts = parse_timestamp(obj["timestamp"])  # normalize tz
            unit_str = str(obj["unit"]).strip()
            rate = to_kg_per_h(float(obj["value"]), cast(Unit, unit_str))
            records.append(
                EmissionRecord(
                    timestamp=ts,
                    site_id=str(obj["site_id"]),
                    region_id=str(obj["region_id"]),
                    emission_rate_kg_per_h=rate,
                    source="jsonl",
                )
            )
    return records


def append_file(path: Path, records: Iterable[EmissionRecord]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fp:
        return write_records(fp, records)


def read_file(path: Path) -> list[EmissionRecord]:
    with path.open("r", encoding="utf-8") as fp:
        return read_records(fp)


class JsonlStore(Store):
    """A simple JSONL-backed Store implementation.

    Notes:
        This implementation reads the whole file for queries; it favors simplicity.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Ensure file exists
        if not self.path.exists():
            self.path.touch()

    def _all_from_disk(self) -> list[EmissionRecord]:
        try:
            return read_file(self.path)
        except FileNotFoundError:
            return []

    def append(self, records: Iterable[EmissionRecord]) -> int:
        return append_file(self.path, records)

    def all(self) -> list[EmissionRecord]:
        return self._all_from_disk()

    def tail(self, n: int) -> list[EmissionRecord]:
        return self._all_from_disk()[-n:]

    def summary(self) -> dict[str, float | int]:
        vals = [r.emission_rate_kg_per_h for r in self._all_from_disk()]
        if not vals:
            return {"count": 0, "mean": 0.0, "min": 0.0, "max": 0.0}
        return {
            "count": len(vals),
            "mean": sum(vals) / len(vals),
            "min": min(vals),
            "max": max(vals),
        }

    def to_dicts(self) -> list[dict[str, float | str]]:
        out: list[dict[str, float | str]] = []
        for r in self._all_from_disk():
            out.append(
                {
                    "timestamp": r.timestamp.astimezone(timezone.utc).isoformat(),
                    "site_id": r.site_id,
                    "region_id": r.region_id,
                    "emission_rate_kg_per_h": r.emission_rate_kg_per_h,
                }
            )
        return out

    def query_time_range(
        self, start: datetime | None, end: datetime | None
    ) -> list[EmissionRecord]:
        def in_range(r: EmissionRecord) -> bool:
            if start and r.timestamp < start:
                return False
            if end and r.timestamp >= end:
                return False
            return True

        return [r for r in self._all_from_disk() if in_range(r)]
