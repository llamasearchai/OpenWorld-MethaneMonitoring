from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

COMMON_FORMATS = (
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%d %H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
)


def parse_timestamp(value: str, tz_default: timezone = timezone.utc) -> datetime:
    """Parse a timestamp string into a datetime object, normalizing to UTC.

    Supports various ISO formats and handles timezone conversion.

    Args:
        value: The timestamp string to parse.
        tz_default: Default timezone if none is provided in the string.

    Returns:
        A timezone-aware datetime in UTC.

    Raises:
        ValueError: If the timestamp format is unrecognized.
    """
    v = value.strip()
    # Handle 'Z' suffix
    if v.endswith("Z"):
        v = v[:-1] + "+0000"
    # Insert timezone colon variants
    if len(v) >= 6 and (v[-3] == ":" and (v[-6] == "+" or v[-6] == "-")):
        v = v[:-3] + v[-2:]
    for fmt in COMMON_FORMATS:
        try:
            dt = datetime.strptime(v, fmt)
            break
        except ValueError:
            continue
    else:
        # Try fromisoformat without timezone colon restriction
        try:
            dt = datetime.fromisoformat(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Unrecognized timestamp format: {value}") from e
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz_default)
    return dt.astimezone(timezone.utc)


def floor_to_window(dt: datetime, seconds: int) -> datetime:
    """Floor a datetime to the start of its time window.

    Args:
        dt: The datetime to floor.
        seconds: The window size in seconds.

    Returns:
        The floored datetime.
    """
    epoch = int(dt.timestamp())
    floored = epoch - (epoch % seconds)
    return datetime.fromtimestamp(floored, tz=timezone.utc)


def windows(start: datetime, end: datetime, seconds: int) -> Iterable[datetime]:
    """Generate window start times from start to end.

    Args:
        start: Start datetime.
        end: End datetime.
        seconds: Window size in seconds.

    Yields:
        Datetime objects for each window start.
    """
    cur = floor_to_window(start, seconds)
    while cur < end:
        yield cur
        cur = datetime.fromtimestamp(cur.timestamp() + seconds, tz=timezone.utc)
