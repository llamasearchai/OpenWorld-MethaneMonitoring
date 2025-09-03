import unittest
from datetime import timezone

from openworld_methane.core.timeutil import floor_to_window, parse_timestamp


class TestTimeUtil(unittest.TestCase):
    def test_parse_timestamp_variants(self):
        t1 = parse_timestamp("2025-01-01T00:00:00Z")
        t2 = parse_timestamp("2025-01-01 00:00:00+00:00")
        t3 = parse_timestamp("2025-01-01T00:00:00+0000")
        self.assertEqual(t1, t2)
        self.assertEqual(t2, t3)
        self.assertEqual(t1.tzinfo, timezone.utc)

    def test_floor_to_window(self):
        t = parse_timestamp("2025-01-01T00:05:31Z")
        f = floor_to_window(t, 300)  # 5 minutes
        self.assertEqual(f.minute, 5)
        self.assertEqual(f.second, 0)


if __name__ == "__main__":
    unittest.main()
