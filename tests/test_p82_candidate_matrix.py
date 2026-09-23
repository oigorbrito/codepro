import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class P82CandidateMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "experiments" / "p82-candidate-matrix.json"
        cls.payload = json.loads(path.read_text(encoding="utf-8"))

    def test_matrix_is_design_only_and_broad(self):
        self.assertEqual(self.payload["status"], "DESIGN_ONLY")
        self.assertGreaterEqual(len(self.payload["candidates"]), 15)

    def test_each_candidate_has_harness_state_and_targets(self):
        for candidate in self.payload["candidates"]:
            self.assertTrue(candidate["id"])
            self.assertTrue(candidate["harness"])
            self.assertTrue(candidate["prior_state"])
            self.assertTrue(candidate["initial_targets"])
            self.assertTrue(set(candidate["initial_targets"]).issubset({"T0", "T1", "T2", "T3", "T4", "T5"}))

    def test_no_candidate_is_marked_as_resolution_evidence(self):
        for candidate in self.payload["candidates"]:
            self.assertNotIn("resolved", candidate["prior_state"])
            self.assertNotIn("promoted", candidate["prior_state"])

    def test_nooa_is_investigation_only(self):
        candidate = next(item for item in self.payload["candidates"] if item["id"] == "nooa/0.0.10")
        self.assertEqual(candidate["prior_state"], "investigation_only")


if __name__ == "__main__":
    unittest.main()
