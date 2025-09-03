import unittest

from openworld_methane.core.units import METHANE_DENSITY_KG_PER_M3, from_kg_per_h, to_kg_per_h


class TestUnits(unittest.TestCase):
    def test_g_per_h(self):
        self.assertAlmostEqual(to_kg_per_h(2500, "g/h"), 2.5)
        self.assertAlmostEqual(from_kg_per_h(2.5, "g/h"), 2500)

    def test_m3_per_h(self):
        self.assertAlmostEqual(to_kg_per_h(1.0, "m3/h"), METHANE_DENSITY_KG_PER_M3)
        self.assertAlmostEqual(from_kg_per_h(METHANE_DENSITY_KG_PER_M3, "m3/h"), 1.0)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            to_kg_per_h(1.0, "lbs/h")


if __name__ == "__main__":
    unittest.main()
