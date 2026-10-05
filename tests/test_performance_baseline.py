import json
import tempfile
import unittest
from pathlib import Path

from arkx.performance_baseline import collect_baseline, write_baseline


class PerformanceBaselineTests(unittest.TestCase):
    def test_baseline_records_measurement_status_and_unknowns(self):
        with tempfile.TemporaryDirectory() as directory:
            report = collect_baseline(directory, samples=2)

        self.assertEqual(report["baseline_type"], "LOCAL_OVERHEAD_BASELINE")
        self.assertEqual(report["interpretation"]["agility_impact"], "NOT_VERIFIED")
        self.assertEqual(len(report["measurements"]), 5)
        for measurement in report["measurements"]:
            self.assertIn(measurement["status"], {"PASS", "BLOCKED"})
            if measurement["status"] == "PASS":
                self.assertEqual(measurement["sample_count"], 2)

    def test_baseline_persists_atomically_as_json(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "evidence" / "baseline.json"
            write_baseline(collect_baseline(directory, samples=1), output)
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(payload["schema_version"], 1)
        self.assertFalse(output.with_name("baseline.json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
