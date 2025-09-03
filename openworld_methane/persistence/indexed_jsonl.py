"""Optimized JSONL store with indexing for improved performance."""

from __future__ import annotations

import json
import pickle
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

from ..core.logging import get_logger, log_error_with_context
from ..models import EmissionRecord
from .jsonl import read_records
from .store import Store


class IndexEntry(NamedTuple):
    """Index entry for fast lookups."""
    offset: int
    length: int
    timestamp: datetime
    site_id: str
    region_id: str


class IndexedJsonlStore(Store):
    """A JSONL-backed Store with indexing for improved performance.
    
    Maintains an index file alongside the JSONL file to enable fast queries
    without reading the entire file every time.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.index_path = path.with_suffix(f"{path.suffix}.idx")
        self.logger = get_logger("persistence.indexed_jsonl")

        # Ensure directories exist
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure files exist
        if not self.path.exists():
            self.path.touch()

        self._index: list[IndexEntry] = []
        self._index_loaded = False

    def _load_index(self) -> None:
        """Load index from disk if it exists."""
        if self._index_loaded:
            return

        try:
            if self.index_path.exists():
                with self.index_path.open("rb") as fp:
                    self._index = pickle.load(fp)
                self.logger.debug("Loaded index", extra={"entry_count": len(self._index)})
            else:
                self._rebuild_index()
        except Exception as e:
            log_error_with_context(
                self.logger,
                "Failed to load index, rebuilding",
                exception=e,
                index_path=str(self.index_path)
            )
            self._rebuild_index()
        finally:
            self._index_loaded = True

    def _save_index(self) -> None:
        """Save index to disk."""
        try:
            with self.index_path.open("wb") as fp:
                pickle.dump(self._index, fp)
            self.logger.debug("Saved index", extra={"entry_count": len(self._index)})
        except Exception as e:
            log_error_with_context(
                self.logger,
                "Failed to save index",
                exception=e,
                index_path=str(self.index_path)
            )

    def _rebuild_index(self) -> None:
        """Rebuild the index by scanning the entire JSONL file."""
        self._index = []

        if not self.path.exists() or self.path.stat().st_size == 0:
            return

        try:
            with self.path.open("r", encoding="utf-8") as fp:
                offset = 0
                while True:
                    line_start = fp.tell()
                    line = fp.readline()
                    if not line:
                        break

                    line = line.strip()
                    if not line:
                        continue

                    try:
                        obj = json.loads(line)
                        from ..core.timeutil import parse_timestamp

                        timestamp = parse_timestamp(obj["timestamp"])
                        entry = IndexEntry(
                            offset=line_start,
                            length=len(line.encode("utf-8")),
                            timestamp=timestamp,
                            site_id=str(obj["site_id"]),
                            region_id=str(obj["region_id"])
                        )
                        self._index.append(entry)

                    except (json.JSONDecodeError, KeyError) as e:
                        self.logger.warning(
                            "Skipping malformed line in JSONL",
                            extra={"offset": line_start, "error": str(e)}
                        )
                        continue

            self._save_index()
            self.logger.info("Rebuilt index", extra={"entry_count": len(self._index)})

        except Exception as e:
            log_error_with_context(
                self.logger,
                "Failed to rebuild index",
                exception=e,
                jsonl_path=str(self.path)
            )
            self._index = []

    def _read_records_by_offsets(self, offsets: list[int]) -> list[EmissionRecord]:
        """Read specific records by their file offsets."""
        if not offsets:
            return []

        records: list[EmissionRecord] = []

        try:
            with self.path.open("r", encoding="utf-8") as fp:
                for offset in sorted(offsets):
                    fp.seek(offset)
                    line = fp.readline().strip()
                    if not line:
                        continue

                    try:
                        obj = json.loads(line)
                        from typing import cast

                        from ..core.timeutil import parse_timestamp
                        from ..core.units import Unit, to_kg_per_h

                        if "emission_rate_kg_per_h" in obj:
                            ts = parse_timestamp(obj["timestamp"])
                            records.append(
                                EmissionRecord(
                                    timestamp=ts,
                                    site_id=str(obj["site_id"]),
                                    region_id=str(obj["region_id"]),
                                    emission_rate_kg_per_h=float(obj["emission_rate_kg_per_h"]),
                                    source="indexed_jsonl",
                                )
                            )
                        else:
                            # fallback conversion
                            ts = parse_timestamp(obj["timestamp"])
                            unit_str = str(obj["unit"]).strip()
                            rate = to_kg_per_h(float(obj["value"]), cast(Unit, unit_str))
                            records.append(
                                EmissionRecord(
                                    timestamp=ts,
                                    site_id=str(obj["site_id"]),
                                    region_id=str(obj["region_id"]),
                                    emission_rate_kg_per_h=rate,
                                    source="indexed_jsonl",
                                )
                            )
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        self.logger.warning(
                            "Skipping malformed record",
                            extra={"offset": offset, "error": str(e)}
                        )
                        continue

        except Exception as e:
            log_error_with_context(
                self.logger,
                "Failed to read records by offsets",
                exception=e,
                offset_count=len(offsets)
            )

        return records

    def append(self, records: Iterable[EmissionRecord]) -> int:
        """Append records and update index."""
        self._load_index()

        # Get current file size for offset calculation
        current_size = self.path.stat().st_size if self.path.exists() else 0

        count = 0
        new_entries: list[IndexEntry] = []

        try:
            with self.path.open("a", encoding="utf-8") as fp:
                for record in records:
                    line_start = fp.tell()

                    obj = {
                        "timestamp": record.timestamp.astimezone(timezone.utc).isoformat(),
                        "site_id": record.site_id,
                        "region_id": record.region_id,
                        "emission_rate_kg_per_h": record.emission_rate_kg_per_h,
                    }
                    line = json.dumps(obj) + "\n"
                    fp.write(line)

                    entry = IndexEntry(
                        offset=line_start,
                        length=len(line.encode("utf-8")),
                        timestamp=record.timestamp,
                        site_id=record.site_id,
                        region_id=record.region_id
                    )
                    new_entries.append(entry)
                    count += 1

            # Update index
            self._index.extend(new_entries)
            self._save_index()

            self.logger.info("Appended records", extra={"count": count})

        except Exception as e:
            log_error_with_context(
                self.logger,
                "Failed to append records",
                exception=e,
                record_count=count
            )
            raise

        return count

    def all(self) -> list[EmissionRecord]:
        """Get all records using fallback for compatibility."""
        # For large files, this could be memory-intensive
        # Consider implementing pagination for production use
        try:
            with self.path.open("r", encoding="utf-8") as fp:
                return read_records(fp)
        except FileNotFoundError:
            return []

    def tail(self, n: int) -> list[EmissionRecord]:
        """Get the last n records using index for efficiency."""
        self._load_index()

        if not self._index:
            return []

        # Get last n entries from index
        tail_entries = self._index[-n:] if len(self._index) >= n else self._index
        offsets = [entry.offset for entry in tail_entries]

        return self._read_records_by_offsets(offsets)

    def summary(self) -> dict[str, float | int]:
        """Calculate summary statistics."""
        # For very large datasets, this could be optimized with streaming calculation
        records = self.all()
        vals = [r.emission_rate_kg_per_h for r in records]

        if not vals:
            return {"count": 0, "mean": 0.0, "min": 0.0, "max": 0.0}

        return {
            "count": len(vals),
            "mean": sum(vals) / len(vals),
            "min": min(vals),
            "max": max(vals),
        }

    def to_dicts(self) -> list[dict[str, float | str]]:
        """Convert all records to dictionaries."""
        records = self.all()
        return [
            {
                "timestamp": r.timestamp.astimezone(timezone.utc).isoformat(),
                "site_id": r.site_id,
                "region_id": r.region_id,
                "emission_rate_kg_per_h": r.emission_rate_kg_per_h,
            }
            for r in records
        ]

    def query_time_range(
        self, start: datetime | None, end: datetime | None
    ) -> list[EmissionRecord]:
        """Query records within a time range using index for efficiency."""
        self._load_index()

        if not self._index:
            return []

        # Filter index entries by time range
        matching_offsets = []
        for entry in self._index:
            if start and entry.timestamp < start:
                continue
            if end and entry.timestamp >= end:
                continue
            matching_offsets.append(entry.offset)

        return self._read_records_by_offsets(matching_offsets)

    def query_by_site(self, site_id: str) -> list[EmissionRecord]:
        """Query records for a specific site using index."""
        self._load_index()

        matching_offsets = [
            entry.offset for entry in self._index
            if entry.site_id == site_id
        ]

        return self._read_records_by_offsets(matching_offsets)

    def query_by_region(self, region_id: str) -> list[EmissionRecord]:
        """Query records for a specific region using index."""
        self._load_index()

        matching_offsets = [
            entry.offset for entry in self._index
            if entry.region_id == region_id
        ]

        return self._read_records_by_offsets(matching_offsets)

    def get_sites(self) -> set[str]:
        """Get all unique site IDs."""
        self._load_index()
        return {entry.site_id for entry in self._index}

    def get_regions(self) -> set[str]:
        """Get all unique region IDs."""
        self._load_index()
        return {entry.region_id for entry in self._index}
