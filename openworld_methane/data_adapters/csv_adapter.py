from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import asdict
from datetime import timezone
from typing import Any, TextIO

from ..core.logging import get_logger
from ..core.security import validate_emission_rate, validate_region_id, validate_site_id
from ..core.timeutil import parse_timestamp
from ..core.units import to_kg_per_h
from ..models import EmissionRecord

REQUIRED_COLUMNS = {"timestamp", "site_id", "region_id", "value", "unit"}


def read_csv(fp: TextIO) -> list[EmissionRecord]:
    """Read CSV data with input validation and error handling."""
    logger = get_logger("data_adapters.csv")

    try:
        reader = csv.DictReader(fp)
        header = {h.strip() for h in reader.fieldnames or []}
        missing = REQUIRED_COLUMNS - header
        if missing:
            raise ValueError(f"Missing required CSV columns: {sorted(missing)}")

        records: list[EmissionRecord] = []
        row_count = 0

        for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
            row_count += 1
            try:
                # Validate and parse timestamp
                ts = parse_timestamp(row["timestamp"])

                # Validate site and region IDs
                site_id = validate_site_id(row["site_id"].strip())
                region_id = validate_region_id(row["region_id"].strip())

                # Validate and convert emission value
                unit = row["unit"].strip()
                raw_value = validate_emission_rate(row["value"])
                value_kg_h = to_kg_per_h(raw_value, unit)  # type: ignore[arg-type]

                # Create record with validated data
                rec = EmissionRecord(
                    timestamp=ts,
                    site_id=site_id,
                    region_id=region_id,
                    emission_rate_kg_per_h=value_kg_h,
                    source="csv",
                    meta={k: v for k, v in row.items() if k not in REQUIRED_COLUMNS},
                )
                records.append(rec)

            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid row {row_num}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error processing row {row_num}: {e}")
                raise ValueError(f"Failed to process row {row_num}: {e}")

        logger.info(f"Successfully processed {len(records)} valid records from CSV")
        return records

    except Exception as e:
        logger.error(f"Failed to read CSV data: {e}")
        raise


def to_dicts(records: Iterable[EmissionRecord]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in records:
        d = asdict(r)
        d["timestamp"] = r.timestamp.astimezone(timezone.utc).isoformat()
        out.append(d)
    return out
