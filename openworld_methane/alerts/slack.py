from __future__ import annotations

import json
from collections.abc import Iterable
from urllib import request

from ..models import Anomaly
from . import Alert


class SlackWebhookAlerter(Alert):
    def __init__(self, *, webhook_url: str, dry_run: bool = False) -> None:
        self.webhook_url = webhook_url
        self.dry_run = dry_run

    def send_text(self, text: str) -> None:
        payload = {"text": text}
        data = json.dumps(payload).encode("utf-8")
        if self.dry_run:
            print(f"[DRY-RUN SLACK] payload={payload}")
            return
        req = request.Request(
            self.webhook_url, data=data, headers={"Content-Type": "application/json"}
        )
        with request.urlopen(req) as resp:  # nosec - used only when configured intentionally
            _ = resp.read()

    def send_anomalies(self, anomalies: Iterable[Anomaly]) -> int:
        anomalies = list(anomalies)
        if not anomalies:
            return 0
        lines = []
        for a in anomalies:
            r = a.record
            lines.append(
                f"{r.timestamp.isoformat()} | site={r.site_id} region={r.region_id} "
                f"rate={r.emission_rate_kg_per_h:.3f} kg/h | z={a.score:.2f}"
            )
        text = "OpenWorld methane anomalies (count={})\n{}".format(len(anomalies), "\n".join(lines))
        self.send_text(text)
        return len(anomalies)
