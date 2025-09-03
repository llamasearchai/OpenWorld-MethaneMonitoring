"""Pluggable alerting backends (email, Slack webhook)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from ..models import Anomaly


class Alert(ABC):
    """Alert interface for notification backends."""

    @abstractmethod
    def send_text(self, text: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def send_anomalies(self, anomalies: Iterable[Anomaly]) -> int:
        """Default anomaly sender using plain text list."""
        anomalies = list(anomalies)
        if not anomalies:
            return 0
        lines = []
        for a in anomalies:
            r = a.record
            lines.append(
                f"{r.timestamp.isoformat()} | site={r.site_id} region={r.region_id} "
                f"rate={r.emission_rate_kg_per_h:.3f} kg/h | score={a.score:.2f} ({a.method})"
            )
        self.send_text("\n".join(lines))
        return len(anomalies)


from .email import EmailAlerter  # noqa: E402
from .slack import SlackWebhookAlerter  # noqa: E402

__all__ = ["Alert", "EmailAlerter", "SlackWebhookAlerter"]
