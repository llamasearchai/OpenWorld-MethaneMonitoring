import unittest
from datetime import datetime, timezone

from openworld_methane.models import EmissionRecord
from openworld_methane.persistence.store import DataStore


class TestPersistence(unittest.TestCase):
    def test_store_append_and_summary(self):
        s = DataStore()
        now = datetime.now(tz=timezone.utc)
        s.append(
            [
                EmissionRecord(
                    timestamp=now, site_id="s1", region_id="r1", emission_rate_kg_per_h=1.0
                ),
                EmissionRecord(
                    timestamp=now, site_id="s1", region_id="r1", emission_rate_kg_per_h=2.0
                ),
            ]
        )
        sm = s.summary()
        self.assertEqual(sm["count"], 2)
        self.assertAlmostEqual(sm["mean"], 1.5)


if __name__ == "__main__":
    unittest.main()
