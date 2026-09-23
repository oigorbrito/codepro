import json
import unittest
from decimal import Decimal
from pathlib import Path

from arkx.composition import Mechanism
from arkx.executor_qualification import ExecutionBudget, ExecutionEnvironment, ExecutorIdentity, QualificationTask
from arkx.p82 import (
    P82Comparability, P82ExperimentConfig, P82Observation, P82ObservationRecord,
    P82RunManifest, P82RunStatus, P82Treatment, TaskSampleManifest, TaskSampleTask,
    TaskStratum, build_p82_plan, compare_run_manifests, p82_manifest, plan_is_comparable,
    summarize_p82,
)


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
    def sample(self, task_revision="task-rev"):
        task = QualificationTask("task-1", task_revision, "acceptance-v1")
        return TaskSampleManifest("sample-1", (TaskSampleTask(task, TaskStratum.MINI_CONTROL, ("upstream",), ("evidence",)),), "sample-rev")

    def make_run(self, treatment="A", **overrides):
        values = {
            "protocol_version": "p8.2-v1", "treatment": p82_manifest()[ord(treatment) - ord("A")],
            "executor": ExecutorIdentity("mini", "1", "adapter", "cfg"), "model": "model-v1",
            "temperature": "0", "reasoning_configuration": "standard",
            "environment": ExecutionEnvironment("repo", "python", "windows", "tools", "env"),
            "task_sample": self.sample(), "attempts": 1, "token_budget": 1000,
            "cost_budget": Decimal("2"), "wall_time_limit": Decimal("60"),
            "verification_identity": "verification-v1", "acceptance_identity": "acceptance-v1",
        }
        values.update(overrides)
        return P82RunManifest(**values)

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

    def test_treatment_only_change_is_comparable(self):
        self.assertEqual(compare_run_manifests(self.make_run("A"), self.make_run("D")), P82Comparability.COMPARABLE)

    def test_model_budget_and_environment_changes_are_not_comparable(self):
        self.assertEqual(compare_run_manifests(self.make_run(), self.make_run(model="other")), P82Comparability.NOT_COMPARABLE)
        self.assertEqual(compare_run_manifests(self.make_run(), self.make_run(token_budget=2000)), P82Comparability.NOT_COMPARABLE)
        self.assertEqual(compare_run_manifests(self.make_run(), self.make_run(environment=ExecutionEnvironment("other", "python", "windows", "tools", "env"))), P82Comparability.NOT_COMPARABLE)

    def test_insufficient_identity_is_indeterminate(self):
        self.assertEqual(compare_run_manifests(self.make_run(model=None), self.make_run("B", model=None)), P82Comparability.INDETERMINATE)

    def test_observation_preserves_missing_metric_and_boolean(self):
        value = P82Observation(P82RunStatus.EXECUTED).to_dict()
        self.assertIsNone(value["cost_to_acceptance"])
        self.assertIsNone(value["verified_acceptance"])

    def test_manifest_and_observation_round_trip_deterministically(self):
        manifest = self.make_run("C")
        self.assertEqual(manifest.to_json(), P82RunManifest.from_dict(json.loads(manifest.to_json())).to_json())
        observation = P82Observation(P82RunStatus.EXECUTED, cost_to_acceptance=Decimal("1.25"))
        self.assertEqual(observation.to_dict(), P82Observation.from_dict(json.loads(json.dumps(observation.to_dict(), default=str))).to_dict())

    def test_execution_does_not_imply_acceptance_or_promotion(self):
        record = P82ObservationRecord(self.make_run(), P82Observation(P82RunStatus.EXECUTED))
        self.assertIsNone(record.observation.verified_acceptance)
        self.assertNotIn("promotion", record.to_dict())

    def test_summary_is_order_independent_and_excludes_non_executed_from_acceptance(self):
        records = (
            P82ObservationRecord(self.make_run("A"), P82Observation(P82RunStatus.NOT_EXECUTED, verified_acceptance=True)),
            P82ObservationRecord(self.make_run("A"), P82Observation(P82RunStatus.EXECUTED, verified_acceptance=False)),
            P82ObservationRecord(self.make_run("D"), P82Observation(P82RunStatus.BLOCKED, verified_acceptance=True)),
        )
        left = tuple(item.to_dict() for item in summarize_p82(records))
        right = tuple(item.to_dict() for item in summarize_p82(tuple(reversed(records))))
        self.assertEqual(left, right)
        self.assertIsNotNone(left[0]["verified_acceptance_rate"])
        self.assertEqual(left[0]["not_executed_count"], 1)
        self.assertEqual(left[3]["blocked_count"], 1)
        self.assertIsNone(left[3]["verified_acceptance_rate"])

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
