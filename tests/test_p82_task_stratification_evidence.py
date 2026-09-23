import json
from pathlib import Path
import unittest


class P82TaskStratificationEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(__file__).parents[1] / "experiments" / "p82-task-stratification-evidence.json"
        self.payload = json.loads(self.path.read_text(encoding="utf-8"))

    def test_design_is_explicitly_non_executed(self):
        self.assertEqual(self.payload["status"], "DESIGN_ONLY")
        self.assertEqual(self.payload["strata"], ["T0", "T1", "T2", "T3", "T4", "T5"])

    def test_external_evidence_is_not_labeled_as_arkx(self):
        for item in self.payload["external_evidence"]:
            self.assertNotEqual(item["class"], "arkx_evidence")
            self.assertTrue(item["source"].startswith("https://"))

    def test_wave0_annotations_are_provisional(self):
        self.assertEqual(self.payload["wave0"]["sympy__sympy-14711"], "T1_PROVISIONAL")
        self.assertEqual(self.payload["wave0"]["sympy__sympy-24443"], "T2_PROVISIONAL")


if __name__ == "__main__":
    unittest.main()
