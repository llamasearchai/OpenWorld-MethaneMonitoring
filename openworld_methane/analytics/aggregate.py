from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime, timedelta

from ..core.timeutil import floor_to_window
from ..models import EmissionRecord, WindowAggregate


def parse_window(window: str) -> int:
    # returns window length in seconds
    window = window.strip().lower()
    if window.endswith("h"):
        return int(float(window[:-1]) * 3600)
    if window.endswith("m"):
        return int(float(window[:-1]) * 60)
    if window.endswith("s"):
        return int(float(window[:-1]))
    raise ValueError("Unsupported window format. Use like '1h', '15m', '30s'.")


def aggregate(records: Iterable[EmissionRecord], window: str) -> list[WindowAggregate]:
    sec = parse_window(window)
    buckets: dict[tuple[datetime, str, str], list[float]] = defaultdict(list)

    for r in records:
        start = floor_to_window(r.timestamp, sec)
        key = (start, r.site_id, r.region_id)
        buckets[key].append(r.emission_rate_kg_per_h)

    results: list[WindowAggregate] = []
    for (start, site_id, region_id), values in sorted(
        buckets.items(), key=lambda x: (x[0][0], x[0][1], x[0][2])
    ):
        count = len(values)
        mean = sum(values) / count
        min_v = min(values)
        max_v = max(values)
        # sum kg over the window approximated as rate * window (h) for each sample
        # This is simplistic; assumes each sample represents the window interval.
        sum_kg = sum(v * (sec / 3600.0) for v in values)
        results.append(
            WindowAggregate(
                start=start,
                end=start + timedelta(seconds=sec),
                site_id=site_id,
                region_id=region_id,
                count=count,
                mean_kg_per_h=mean,
                min_kg_per_h=min_v,
                max_kg_per_h=max_v,
                sum_kg=sum_kg,
            )
        )
    return results
