import unittest
from datetime import datetime, timezone

from openworld_methane.compliance.rules import ThresholdRule, evaluate_threshold_rule
from openworld_methane.models import EmissionRecord


class TestCompliance(unittest.TestCase):
    def test_threshold_rule(self):
        now = datetime.now(tz=timezone.utc)
        recs = [
            EmissionRecord(timestamp=now, site_id="s1", region_id="r1", emission_rate_kg_per_h=12.0)
        ]
        rule = ThresholdRule(rule_id="T1", threshold_kg_per_h=10.0, due_days=7)
        rems = evaluate_threshold_rule(recs, rule)
        self.assertEqual(len(rems), 1)
        self.assertEqual(rems[0].site_id, "s1")
        self.assertEqual(rems[0].status, "open")


if __name__ == "__main__":
    unittest.main()
