import io
import json
import unittest
from datetime import datetime, timezone

from openworld_methane.dashboards.ascii import render_dashboard
from openworld_methane.models import EmissionRecord
from openworld_methane.reporting.report import write_json_report


class TestDashboardAndReporting(unittest.TestCase):
    def test_dashboard(self):
        now = datetime.now(tz=timezone.utc)
        recs = [
            EmissionRecord(timestamp=now, site_id="s1", region_id="r1", emission_rate_kg_per_h=1.0),
            EmissionRecord(timestamp=now, site_id="s1", region_id="r1", emission_rate_kg_per_h=2.0),
        ]
        out = render_dashboard(recs)
        self.assertIn("OpenWorld Methane Dashboard", out)
        self.assertIn("Records: 2", out)

    def test_report_json(self):
        now = datetime.now(tz=timezone.utc)
        recs = [
            EmissionRecord(timestamp=now, site_id="s1", region_id="r1", emission_rate_kg_per_h=1.0)
        ]
        buf = io.StringIO()
        write_json_report(buf, records=recs)
        data = json.loads(buf.getvalue())
        self.assertIn("records", data)
        self.assertIn("records_summary", data)


if __name__ == "__main__":
    unittest.main()
