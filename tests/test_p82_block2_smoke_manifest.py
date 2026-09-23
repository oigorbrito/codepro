import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class P82Block2SmokeManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "experiments" / "p82-block2-smoke-manifest.json"
        cls.payload = json.loads(path.read_text(encoding="utf-8"))

    def test_manifest_is_predeclared_and_model_free(self):
        self.assertEqual(self.payload["status"], "PREDECLARED")
        self.assertEqual(self.payload["frozen"]["model_calls"], 0)
        self.assertIsNone(self.payload["frozen"]["provider"])

    def test_has_one_cell_per_initial_stratum(self):
        cells = self.payload["cells"]
        self.assertEqual([cell["stratum"] for cell in cells], ["T0", "T1", "T2"])
        self.assertEqual(len({cell["cell_id"] for cell in cells}), 3)

    def test_promotion_rule_preserves_evidence_boundary(self):
        rule = self.payload["promotion_rule"]
        self.assertIn("does not qualify a model", rule)
        self.assertIn("B1", rule)
        self.assertIn("C1", rule)


if __name__ == "__main__":
    unittest.main()
