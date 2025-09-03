from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

from ..models import EmissionRecord


@runtime_checkable
class Store(Protocol):
    def append(self, records: Iterable[EmissionRecord]) -> int: ...
    def all(self) -> list[EmissionRecord]: ...
    def tail(self, n: int) -> list[EmissionRecord]: ...
    def summary(self) -> dict[str, Any]: ...
    def to_dicts(self) -> list[dict[str, Any]]: ...
    def query_time_range(
        self, start: datetime | None, end: datetime | None
    ) -> list[EmissionRecord]: ...


class InMemoryStore:
    def __init__(self) -> None:
        self._records: list[EmissionRecord] = []

    def append(self, records: Iterable[EmissionRecord]) -> int:
        n0 = len(self._records)
        self._records.extend(records)
        return len(self._records) - n0

    def all(self) -> list[EmissionRecord]:
        return list(self._records)

    def tail(self, n: int) -> list[EmissionRecord]:
        return self._records[-n:]

    def summary(self) -> dict[str, Any]:
        vals = [r.emission_rate_kg_per_h for r in self._records]
        if not vals:
            return {"count": 0, "mean": 0.0, "min": 0.0, "max": 0.0}
        return {
            "count": len(vals),
            "mean": sum(vals) / len(vals),
            "min": min(vals),
            "max": max(vals),
        }

    def to_dicts(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for r in self._records:
            d = asdict(r)
            d["timestamp"] = r.timestamp.astimezone(timezone.utc).isoformat()
            out.append(d)
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

        return [r for r in self._records if in_range(r)]


# Backwards compatibility for existing imports
DataStore = InMemoryStore
