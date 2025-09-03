import unittest
from datetime import datetime, timezone

from openworld_methane.alerts.email import EmailAlerter
from openworld_methane.alerts.slack import SlackWebhookAlerter
from openworld_methane.analytics.anomaly import detect_anomalies
from openworld_methane.models import EmissionRecord


class TestAlerts(unittest.TestCase):
    def _anomalies(self):
        now = datetime.now(tz=timezone.utc)
        records = [
            EmissionRecord(timestamp=now, site_id="s1", region_id="r1", emission_rate_kg_per_h=v)
            for v in [1.0, 1.1, 10.0, 0.9]
        ]
        return detect_anomalies(records, z_threshold=3.5)

    def test_email_dry_run(self):
        alerter = EmailAlerter(
            smtp_host="localhost",
            sender="noreply@example.com",
            recipients=["ops@example.com"],
            dry_run=True,
        )
        count = alerter.send_anomalies(self._anomalies())
        self.assertGreaterEqual(count, 1)

    def test_slack_dry_run(self):
        alerter = SlackWebhookAlerter(
            webhook_url="https://hooks.slack.com/services/T000/B000/XXX", dry_run=True
        )
        count = alerter.send_anomalies(self._anomalies())
        self.assertGreaterEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
