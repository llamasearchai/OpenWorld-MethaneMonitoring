import io
import unittest
from datetime import datetime, timezone

from openworld_methane.models import EmissionRecord
from openworld_methane.persistence.jsonl import read_records, write_records


class TestJsonl(unittest.TestCase):
    def test_write_and_read(self):
        now = datetime.now(tz=timezone.utc)
        recs = [
            EmissionRecord(timestamp=now, site_id="s1", region_id="r1", emission_rate_kg_per_h=1.23)
        ]
        buf = io.StringIO()
        self.assertEqual(write_records(buf, recs), 1)
        buf.seek(0)
        recs2 = read_records(buf)
        self.assertEqual(len(recs2), 1)
        self.assertAlmostEqual(recs2[0].emission_rate_kg_per_h, 1.23)


if __name__ == "__main__":
    unittest.main()
