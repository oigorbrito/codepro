import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class P82BlockPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "experiments" / "p82-block-plan.json"
        cls.plan = json.loads(path.read_text(encoding="utf-8"))

    def test_plan_is_design_only(self):
        self.assertEqual(self.plan["status"], "DESIGN_ONLY")

    def test_blocks_are_ordered_and_unique(self):
        blocks = self.plan["blocks"]
        ids = [block["id"] for block in blocks]
        self.assertEqual(ids, [f"BLOCK_{index}" for index in range(7)])
        self.assertEqual(len(ids), len(set(ids)))

    def test_block_four_is_the_only_baseline_execution_block(self):
        executable = [
            block["id"] for block in self.plan["blocks"]
            if "execution" in block and "only the predeclared tasks" in block["execution"]
        ]
        self.assertEqual(executable, ["BLOCK_4"])

    def test_global_rules_keep_mechanisms_closed(self):
        rules = " ".join(self.plan["global_rules"])
        self.assertIn("B1 and C1 contracts may be tested", rules)
        self.assertIn("their operational mechanisms remain disabled", rules)
        self.assertIn("D1 is not executable", rules)


if __name__ == "__main__":
    unittest.main()
