import unittest
from datetime import datetime, timezone

from openworld_methane.dashboards.http import render_html
from openworld_methane.models import EmissionRecord
from openworld_methane.persistence.store import DataStore


class TestHttpDashboard(unittest.TestCase):
    def test_render_html_contains_summary(self):
        store = DataStore()
        now = datetime.now(tz=timezone.utc)
        store.append(
            [
                EmissionRecord(
                    timestamp=now, site_id="s1", region_id="r1", emission_rate_kg_per_h=1.0
                ),
                EmissionRecord(
                    timestamp=now, site_id="s2", region_id="r1", emission_rate_kg_per_h=2.0
                ),
            ]
        )
        html = render_html(store)
        self.assertIn("OpenWorld Methane", html)
        self.assertIn("Records: 2", html)


if __name__ == "__main__":
    unittest.main()
