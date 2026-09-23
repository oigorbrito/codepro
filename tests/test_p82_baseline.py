import tempfile
import unittest
from pathlib import Path

from arkx.p82 import P82RunStatus, P82Treatment, TaskStratum
from arkx.p82_baseline import (
    AcceptanceDecision,
    BaselineExecutionState,
    BaselineRunConfig,
    BaselineSampleManifest,
    ExplicitVerificationAcceptance,
    MiniSweAgentHeadlessRunner,
    ProspectiveTask,
    VerificationResult,
    VerificationState,
    baseline_observation,
)


def task(workspace):
    return ProspectiveTask(
        "task-1", "swebench-verified@v1", "owner/repo", "abc123", "fix the bug",
        TaskStratum.MINI_CONTROL, "stable control", "2026-09-23T00:00:00Z", "p8.2a-v1",
        "verification-v1", "acceptance-v1", str(workspace),
    )


def config(root, **overrides):
    values = {
        "provider": "test-provider", "model": "test-model", "model_version": "v1",
        "temperature": "0", "reasoning_configuration": "none", "max_tokens": 100,
        "model_configuration": None,
        "max_cost": "1", "wall_time_seconds": 10, "mini_version": "2.4.6",
        "python_executable": "python", "runner_version": "p8.2a-runner-v1",
        "artifact_root": str(root), "treatment": P82Treatment.A,
    }
    values.update(overrides)
    return BaselineRunConfig(**values)


class P82BaselineTests(unittest.TestCase):
    def test_headless_runner_uses_fake_invoker_and_captures_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            workspace.mkdir()
            calls = []

            def fake_invoker(run_task, run_config, trajectory):
                calls.append((run_task.task_id, run_config.treatment, trajectory.name))
                trajectory.write_text("{}", encoding="utf-8")
                return 0, "executor-log", {"calls": 1}

            result = MiniSweAgentHeadlessRunner(fake_invoker).run(task(workspace), config(Path(directory) / "artifacts"))
            self.assertEqual(result.state, BaselineExecutionState.COMPLETED)
            self.assertEqual(calls, [("task-1", P82Treatment.A, "trajectory.json")])
            self.assertTrue(Path(result.log_path).exists())
            self.assertTrue(Path(result.diff_path).exists())
            self.assertEqual(result.treatment, "A")

    def test_missing_model_or_provider_is_blocked_without_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            result = MiniSweAgentHeadlessRunner().run(task(directory), config(directory, model=None))
            self.assertEqual(result.state, BaselineExecutionState.BLOCKED)
            self.assertIn("model", result.failure)

    def test_rerun_does_not_overwrite_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = MiniSweAgentHeadlessRunner(lambda *_: (0, "", None))
            first = runner.run(task(directory), config(directory), attempt=1)
            second = runner.run(task(directory), config(directory), attempt=1)
            third = runner.run(task(directory), config(directory), attempt=2)
            self.assertEqual(first.state, BaselineExecutionState.COMPLETED)
            self.assertEqual(second.state, BaselineExecutionState.BLOCKED)
            self.assertEqual(third.state, BaselineExecutionState.COMPLETED)

    def test_acceptance_is_explicit_and_preserves_indeterminate(self):
        authority = ExplicitVerificationAcceptance("acceptance-v1")
        result = authority.decide(VerificationResult(VerificationState.INDETERMINATE, "verification-v1", (), (), ()))
        self.assertEqual(result.decision, AcceptanceDecision.INDETERMINATE)
        self.assertEqual(result.authority, "acceptance-v1")

    def test_verification_pass_is_not_execution_success_or_runner_acceptance(self):
        execution = type("Execution", (), {"state": BaselineExecutionState.COMPLETED})()
        verification = VerificationResult(VerificationState.PASS, "verification-v1", ("pytest",), ("0",), ("log",))
        observation = baseline_observation(execution, verification, None)
        self.assertEqual(observation.status, P82RunStatus.EXECUTED)
        self.assertIsNone(observation.verified_acceptance)

    def test_executor_failure_is_not_task_rejection(self):
        execution = type("Execution", (), {"state": BaselineExecutionState.EXECUTOR_FAILED})()
        observation = baseline_observation(execution, None, None)
        self.assertIsNone(observation.verified_acceptance)
        self.assertEqual(observation.status, P82RunStatus.EXECUTED)

    def test_baseline_rejects_non_a_treatment(self):
        with self.assertRaises(ValueError):
            config("artifacts", treatment=P82Treatment.B)

    def test_prospective_sample_manifest_is_deterministic(self):
        first = task("workspace-a")
        second = ProspectiveTask(
            "task-2", "dataset", "repo", "def456", "another task", TaskStratum.LOCALIZATION_CONTEXT,
            "localization diversity", "2026-09-23T00:00:00Z", "p8.2a-v1", "verification-v1", "acceptance-v1", "workspace-b",
        )
        left = BaselineSampleManifest("wave-0", "baseline-smoke", "predeclared diversity rule", (second, first))
        right = BaselineSampleManifest("wave-0", "baseline-smoke", "predeclared diversity rule", (first, second))
        self.assertEqual(left.to_json(), right.to_json())


if __name__ == "__main__":
    unittest.main()
