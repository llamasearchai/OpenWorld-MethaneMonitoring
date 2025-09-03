import unittest

from openworld_methane.cli import main


class TestCLI(unittest.TestCase):
    def test_simulate_and_analyze(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "sim.json"
            self.assertEqual(
                main(
                    [
                        "simulate",
                        str(out),
                        "--rows",
                        "20",
                        "--sites",
                        "2",
                        "--regions",
                        "1",
                        "--spike-prob",
                        "0.3",
                    ]
                ),
                0,
            )
            self.assertTrue(out.exists())
            # Analyze
            self.assertEqual(main(["analyze", str(out)]), 0)

    def test_ingest_csv(self):
        import tempfile
        from pathlib import Path
        from textwrap import dedent

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "data.csv"
            p.write_text(
                dedent(
                    """
                timestamp,site_id,region_id,value,unit
                2025-01-01T00:00:00Z,s1,r1,2500,g/h
                """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            self.assertEqual(main(["ingest", str(p)]), 0)


if __name__ == "__main__":
    unittest.main()
