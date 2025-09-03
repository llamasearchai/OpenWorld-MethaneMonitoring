from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class EmissionRecord:
    """Represents a single methane emission measurement record.

    Attributes:
        timestamp: The UTC timestamp of the measurement.
        site_id: Identifier for the emission site.
        region_id: Identifier for the region containing the site.
        emission_rate_kg_per_h: Emission rate in kg/h.
        source: Source of the data (e.g., 'csv', 'json').
        meta: Optional additional metadata as a dictionary.
    """

    timestamp: datetime
    site_id: str
    region_id: str
    emission_rate_kg_per_h: float
    source: str = "unknown"
    meta: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Ensure timestamp is timezone-aware UTC."""
        if self.timestamp.tzinfo is None:
            object.__setattr__(self, "timestamp", self.timestamp.replace(tzinfo=timezone.utc))
        else:
            object.__setattr__(self, "timestamp", self.timestamp.astimezone(timezone.utc))


@dataclass(frozen=True)
class Anomaly:
    """Represents a detected anomaly in emission data.

    Attributes:
        record: The emission record that is anomalous.
        score: The anomaly score (e.g., Z-score).
        method: The detection method used (e.g., 'robust_z').
        threshold: The threshold used for detection.
    """

    record: EmissionRecord
    score: float
    method: str
    threshold: float


@dataclass(frozen=True)
class WindowAggregate:
    """Represents aggregated emission data over a time window.

    Attributes:
        start: Start timestamp of the window.
        end: End timestamp of the window.
        site_id: Site identifier.
        region_id: Region identifier.
        count: Number of records in the window.
        mean_kg_per_h: Mean emission rate in kg/h.
        min_kg_per_h: Minimum emission rate in kg/h.
        max_kg_per_h: Maximum emission rate in kg/h.
        sum_kg: Total emissions in kg over the window.
    """

    start: datetime
    end: datetime
    site_id: str
    region_id: str
    count: int
    mean_kg_per_h: float
    min_kg_per_h: float
    max_kg_per_h: float
    sum_kg: float


@dataclass(frozen=True)
class Remediation:
    """Represents a remediation action for compliance.

    Attributes:
        site_id: Site identifier.
        region_id: Region identifier.
        detected_at: Timestamp when the issue was detected.
        due_by: Deadline for remediation.
        status: Status of the remediation (e.g., 'open', 'in_progress', 'resolved', 'overdue').
        rule_id: Identifier of the rule that triggered this remediation.
        details: Description of the remediation required.
    """

    site_id: str
    region_id: str
    detected_at: datetime
    due_by: datetime
    status: str  # open, in_progress, resolved, overdue
    rule_id: str
    details: str
