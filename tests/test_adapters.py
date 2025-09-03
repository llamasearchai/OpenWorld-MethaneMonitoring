import io
import json
import unittest

from openworld_methane.data_adapters.csv_adapter import read_csv
from openworld_methane.data_adapters.json_adapter import read_json


class TestAdapters(unittest.TestCase):
    def test_csv_adapter(self):
        buf = io.StringIO()
        buf.write("timestamp,site_id,region_id,value,unit\n")
        buf.write("2025-01-01T00:00:00Z,s1,r1,2500,g/h\n")
        buf.seek(0)
        records = read_csv(buf)
        self.assertEqual(len(records), 1)
        self.assertAlmostEqual(records[0].emission_rate_kg_per_h, 2.5)

    def test_json_adapter(self):
        data = [
            {
                "timestamp": "2025-01-01T00:00:00Z",
                "site_id": "s1",
                "region_id": "r1",
                "value": 1.0,
                "unit": "m3/h",
            }
        ]
        buf = io.StringIO(json.dumps(data))
        records = read_json(buf)
        self.assertEqual(len(records), 1)
        self.assertGreater(records[0].emission_rate_kg_per_h, 0)


if __name__ == "__main__":
    unittest.main()
