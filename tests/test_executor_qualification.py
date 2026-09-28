import json
import unittest
from decimal import Decimal
from pathlib import Path

from arkx.composition import Mechanism, Treatment
from arkx.executor_qualification import (
    ComparisonAxis,
    ExecutionEnvironment,
    ExecutionOutcome,
    ExecutionBudget,
    ExecutorIdentity,
    ExecutorObservation,
    ExecutorTrial,
    QualificationExperiment,
    QualificationStatus,
    QualificationTask,
    assess_trial,
    compare_trials,
    summarize_experiment,
    validate_paired_executor_experiment,
)


def trial(**overrides):
    values = {
        "executor": ExecutorIdentity("executor", "1.0", "external", "config-a"),
        "task": QualificationTask("task", "rev-1", "acceptance-v1"),
        "model": "model-1",
        "environment": ExecutionEnvironment("repo-1", "python-3.11", "windows", "toolchain-1", "env-a"),
        "budget": ExecutionBudget(1000, Decimal("2.00"), Decimal("60"), 3, 3),
        "treatment": Treatment("A", ()),
        "replicate_id": "rep-1",
        "outcome": ExecutionOutcome.COMPLETED,
        "observation": ExecutorObservation(accepted=True, patch_verified=True, cost=Decimal("1.20"), wall_time_seconds=Decimal("4")),
    }
    values.update(overrides)
    return ExecutorTrial(**values)


class ExecutorQualificationTests(unittest.TestCase):
    def test_executor_identity_serialization_is_deterministic(self):
        identity = ExecutorIdentity("mini", "1.2", "adapter", "digest", ("shell", "file_editing"))
        self.assertEqual(identity.to_json(), '{"advertised_capabilities":["file_editing","shell"],"configuration_digest":"digest","integration_kind":"adapter","name":"mini","version":"1.2"}')
        self.assertEqual(identity.to_json(), ExecutorIdentity("mini", "1.2", "adapter", "digest", ("file_editing", "shell")).to_json())
        self.assertNotEqual(identity, ExecutorIdentity("mini", "1.3", "adapter", "digest", ("shell", "file_editing")))

    def test_advertised_capabilities_are_metadata_not_qualification(self):
        advertised = ExecutorIdentity("mini", "1.2", "adapter", "digest", ("supports_subagents",))
        trial_with_unknown_result = trial(executor=advertised, observation=ExecutorObservation(accepted=None))
        self.assertEqual(assess_trial(trial_with_unknown_result), QualificationStatus.UNKNOWN)

    def test_unknown_metrics_stay_none_and_explicit_zero_stays_zero(self):
        observation = ExecutorObservation(human_interventions=0, retries=None, accepted=None)
        value = observation.to_dict()
        self.assertEqual(value["human_interventions"], 0)
        self.assertIsNone(value["retries"])
        self.assertIsNone(value["accepted"])

    def test_executor_axis_requires_same_controls_and_different_executor(self):
        left = trial()
        right = trial(executor=ExecutorIdentity("other", "1.0", "external", "config-b"), replicate_id="rep-2")
        self.assertEqual(compare_trials(left, right, ComparisonAxis.EXECUTOR), QualificationStatus.QUALIFIABLE)
        changed = trial(task=QualificationTask("other-task", "rev-1", "acceptance-v1"), replicate_id="rep-2")
        self.assertEqual(compare_trials(left, changed, ComparisonAxis.EXECUTOR), QualificationStatus.INCOMPARABLE)

    def test_treatment_axis_requires_same_executor_and_different_treatment(self):
        left = trial()
        right = trial(treatment=Treatment("B", (Mechanism.P1_CHARACTERIZATION,)), replicate_id="rep-2")
        self.assertEqual(compare_trials(left, right, ComparisonAxis.TREATMENT), QualificationStatus.QUALIFIABLE)
        changed = trial(executor=ExecutorIdentity("other", "1.0", "external", "config-b"), replicate_id="rep-2")
        self.assertEqual(compare_trials(left, changed, ComparisonAxis.TREATMENT), QualificationStatus.INCOMPARABLE)

    def test_infrastructure_failure_is_blocked_not_rejected(self):
        failed = trial(outcome=ExecutionOutcome.INFRASTRUCTURE_FAILED, observation=ExecutorObservation(accepted=None))
        self.assertEqual(assess_trial(failed), QualificationStatus.BLOCKED)
        self.assertIsNone(failed.observation.accepted)

    def test_completed_trial_does_not_infer_acceptance(self):
        unknown = trial(observation=ExecutorObservation(accepted=None))
        self.assertEqual(assess_trial(unknown), QualificationStatus.UNKNOWN)

    def test_incomplete_executor_or_environment_identity_is_not_qualifiable(self):
        missing_executor_identity = trial(
            executor=ExecutorIdentity("executor", None, "external", None),
        )
        missing_environment_identity = trial(
            environment=ExecutionEnvironment("repo-1", "python-3.11", "windows", "toolchain-1", None),
        )
        self.assertEqual(assess_trial(missing_executor_identity), QualificationStatus.UNKNOWN)
        self.assertEqual(assess_trial(missing_environment_identity), QualificationStatus.UNKNOWN)

    def test_paired_report_records_incomplete_identity(self):
        experiment = QualificationExperiment(
            (
                trial(executor=ExecutorIdentity("executor", None, "external", None)),
                trial(executor=ExecutorIdentity("other", "1.0", "external", "config-b"), replicate_id="rep-1"),
            ),
            ComparisonAxis.EXECUTOR,
            verifier_identity="verifier-v1",
            instrumentation_identity="telemetry-v1",
        )
        report = validate_paired_executor_experiment(experiment)
        self.assertEqual(report.status, QualificationStatus.UNKNOWN)
        self.assertIn("IDENTITY_INCOMPLETE", report.reason_codes)

    def test_patch_verification_does_not_infer_acceptance(self):
        unknown = trial(observation=ExecutorObservation(accepted=None, patch_verified=True))
        self.assertIsNone(unknown.observation.accepted)
        self.assertEqual(assess_trial(unknown), QualificationStatus.UNKNOWN)

    def test_inconsistent_false_pass_observation_is_blocked(self):
        invalid = trial(observation=ExecutorObservation(accepted=False, patch_verified=False, false_pass=True))
        self.assertEqual(assess_trial(invalid), QualificationStatus.BLOCKED)

    def test_summary_has_no_winner_and_preserves_missing_metrics(self):
        experiment = QualificationExperiment((trial(), trial(observation=ExecutorObservation(accepted=None))), ComparisonAxis.EXECUTOR)
        summary = summarize_experiment(experiment)
        self.assertEqual(summary.qualifiable_trial_count, 1)
        self.assertEqual(summary.acceptance_rate, Decimal("1"))
        self.assertIsNone(summary.false_pass_rate)
        self.assertEqual(summary.median_wall_time_seconds, Decimal("4"))
        self.assertNotIn("winner", summary.to_json())
        self.assertNotIn("PASS", summary.to_json())

    def test_zero_metric_is_included_in_summary(self):
        zero = trial(observation=ExecutorObservation(accepted=False, cost=Decimal("0"), wall_time_seconds=Decimal("0")))
        summary = summarize_experiment(QualificationExperiment((zero,), ComparisonAxis.EXECUTOR))
        self.assertEqual(summary.median_cost, Decimal("0"))
        self.assertEqual(summary.median_wall_time_seconds, Decimal("0"))

    def test_replicates_are_preserved_and_serialized_deterministically(self):
        experiment = QualificationExperiment((trial(replicate_id="rep-2"), trial(replicate_id="rep-1")), ComparisonAxis.EXECUTOR)
        payload = json.loads(experiment.to_json())
        self.assertEqual([item["replicate_id"] for item in payload["trials"]], ["rep-1", "rep-2"])

    def test_module_has_no_execution_integration_imports(self):
        source = (Path(__file__).parents[1] / "src" / "arkx" / "executor_qualification.py").read_text(encoding="utf-8")
        for forbidden in ("subprocess", "openhands", "swe-agent", "mini-swe-agent", "requests", "httpx"):
            self.assertNotIn(forbidden, source.lower())

    def test_fixture_is_classified_as_qualification_fixture(self):
        path = Path(__file__).parents[1] / "experiments" / "executor-qualification-fixture.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(value["fixture_type"], "EXECUTOR_QUALIFICATION_FIXTURE")
        self.assertEqual(value["comparison_axes"], ["EXECUTOR", "TREATMENT"])

    def test_paired_protocol_requires_shared_verifier_and_instrumentation(self):
        experiment = QualificationExperiment(
            (trial(), trial(executor=ExecutorIdentity("other", "1.0", "external", "config-b"), replicate_id="rep-1")),
            ComparisonAxis.EXECUTOR,
        )
        report = validate_paired_executor_experiment(experiment)
        self.assertEqual(report.status, QualificationStatus.UNKNOWN)
        self.assertIn("VERIFIER_IDENTITY_MISSING", report.reason_codes)
        self.assertIn("INSTRUMENTATION_IDENTITY_MISSING", report.reason_codes)

    def test_paired_protocol_accepts_complete_controlled_cells_without_ranking(self):
        experiment = QualificationExperiment(
            (trial(), trial(executor=ExecutorIdentity("other", "1.0", "external", "config-b"), replicate_id="rep-1")),
            ComparisonAxis.EXECUTOR,
            verifier_identity="verifier-v1",
            instrumentation_identity="telemetry-v1",
        )
        report = validate_paired_executor_experiment(experiment)
        self.assertEqual(report.status, QualificationStatus.QUALIFIABLE)
        self.assertEqual(report.executor_names, ("executor", "other"))
        self.assertNotIn("winner", report.to_json())

    def test_paired_protocol_rejects_missing_executor_cell(self):
        experiment = QualificationExperiment(
            (trial(),),
            ComparisonAxis.EXECUTOR,
            verifier_identity="verifier-v1",
            instrumentation_identity="telemetry-v1",
        )
        report = validate_paired_executor_experiment(experiment)
        self.assertEqual(report.status, QualificationStatus.INCOMPARABLE)
        self.assertIn("AT_LEAST_TWO_EXECUTORS_REQUIRED", report.reason_codes)


if __name__ == "__main__":
    unittest.main()
