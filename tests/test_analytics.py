import unittest

from openworld_methane.analytics.aggregate import aggregate
from openworld_methane.analytics.anomaly import detect_anomalies, detect_anomalies_seasonal
from openworld_methane.core.timeutil import parse_timestamp
from openworld_methane.models import EmissionRecord


def _make_records(vals):
    base_ts = parse_timestamp("2025-01-01T00:00:00Z")
    recs = []
    for i, v in enumerate(vals):
        ts = parse_timestamp((base_ts).isoformat())
        # Space by minutes
        ts = ts.fromtimestamp(base_ts.timestamp() + 60 * i, tz=base_ts.tzinfo)
        recs.append(
            EmissionRecord(timestamp=ts, site_id="s1", region_id="r1", emission_rate_kg_per_h=v)
        )
    return recs


class TestAnalytics(unittest.TestCase):
    def test_aggregate(self):
        recs = _make_records([1.0, 2.0, 3.0])
        aggs = aggregate(recs, "2m")
        # Two buckets: minutes 0-2 and 2-4
        self.assertEqual(len(aggs), 2)
        self.assertAlmostEqual(aggs[0].mean_kg_per_h, 1.5)
        self.assertEqual(aggs[0].count, 2)

    def test_anomaly(self):
        recs = _make_records([1.0, 1.1, 1.2, 10.0, 1.0])
        anomalies = detect_anomalies(recs, z_threshold=3.5)
        self.assertTrue(any(a.record.emission_rate_kg_per_h == 10.0 for a in anomalies))

    def test_anomaly_seasonal(self):
        # Build a seasonal series with a spike
        values = [1.0, 2.0] * 12  # period 2
        values[10] = 20.0  # spike
        recs = _make_records(values)
        anomalies = detect_anomalies_seasonal(recs, period=2, z_threshold=3.5)
        self.assertTrue(any(a.record.emission_rate_kg_per_h == 20.0 for a in anomalies))


if __name__ == "__main__":
    unittest.main()
