import json
import unittest
from decimal import Decimal
from pathlib import Path

from arkx.composition import Mechanism
from arkx.executor_qualification import ExecutionBudget, ExecutionEnvironment, ExecutorIdentity, QualificationTask
from arkx.p82 import P82ExperimentConfig, P82Treatment, build_p82_plan, p82_manifest, plan_is_comparable


def config(**overrides):
    values = {
        "executor": ExecutorIdentity("mini-swe-agent", "1.0", "adapter", "mini-config"),
        "model": "claude-4-sonnet-20250514",
        "environment": ExecutionEnvironment("repo-rev", "python-3.11", "windows", "toolchain", "env-digest"),
        "budget": ExecutionBudget(1000, Decimal("2"), Decimal("60"), 1, 1),
        "tasks": (QualificationTask("task-1", "task-rev", "acceptance-v1"),),
    }
    values.update(overrides)
    return P82ExperimentConfig(**values)


class P82Tests(unittest.TestCase):
    def test_manifest_is_exactly_abcd(self):
        manifest = p82_manifest()
        self.assertEqual(tuple(t.name for t in manifest), tuple(item.value for item in P82Treatment))
        self.assertEqual(manifest[0].enabled_mechanisms, ())
        self.assertEqual(manifest[1].enabled_mechanisms, (Mechanism.P8_SAFE_EDITOR,))
        self.assertEqual(manifest[2].enabled_mechanisms, (Mechanism.P8_ENHANCED_REPOSITORY_CONTEXT,))
        self.assertEqual(manifest[3].enabled_mechanisms, (Mechanism.P8_SAFE_EDITOR, Mechanism.P8_ENHANCED_REPOSITORY_CONTEXT))

    def test_plan_is_cartesian_product_without_execution(self):
        plan = build_p82_plan(config(tasks=(QualificationTask("a", "r", "v"), QualificationTask("b", "r", "v")), replicate_ids=("r2", "r1")))
        self.assertEqual(len(plan.trials), 16)
        self.assertEqual([trial.replicate_id for trial in plan.trials[:4]], ["r1"] * 4)
        self.assertNotIn("accepted", plan.to_json())
        self.assertNotIn("outcome", plan.to_json())

    def test_missing_control_evidence_stays_unknown(self):
        self.assertIsNone(plan_is_comparable(build_p82_plan(config(model=None))))
        self.assertTrue(plan_is_comparable(build_p82_plan(config(verification_contract="verification-v1", acceptance_authority="independent-v1"))))

    def test_config_rejects_duplicate_tasks_and_replicates(self):
        task = QualificationTask("a", "r", "v")
        with self.assertRaises(ValueError):
            config(tasks=(task, task))
        with self.assertRaises(ValueError):
            config(replicate_ids=("r1", "r1"))

    def test_fixture_is_p82_design(self):
        path = Path(__file__).parents[1] / "experiments" / "p82-minimal-mechanism-trial-fixture.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(value["fixture_type"], "P82_MINIMAL_MECHANISM_TRIAL")
        self.assertEqual(value["treatments"], ["A", "B", "C", "D"])


if __name__ == "__main__":
    unittest.main()
