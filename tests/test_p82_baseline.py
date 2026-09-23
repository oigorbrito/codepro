import tempfile
import unittest
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from arkx.p82 import P82RunStatus, P82Treatment, TaskStratum
from arkx.harness import RunManifest, RunState
from arkx.harness import load_attempt
from arkx.p82_baseline import (
    AcceptanceDecision,
    BaselineExecutionState,
    BaselineRunConfig,
    BaselineSampleManifest,
    ExplicitVerificationAcceptance,
    MiniSweAgentHeadlessRunner,
    P82BaselineExecutorAdapter,
    ProspectiveTask,
    RunnerFailureCategory,
    VerificationResult,
    VerificationState,
    baseline_observation,
)
from arkx.execution import ExecutionRequest


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
    def test_subprocess_invoker_passes_limits_and_captures_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            workspace.mkdir()
            runner = MiniSweAgentHeadlessRunner()
            completed = type("Completed", (), {
                "returncode": 0,
                "stdout": '{"result":"done","usage":{"model_calls":3,"cost":0.25}}\n',
                "stderr": "worker log\n",
            })()
            with patch("arkx.p82_baseline.subprocess.run", return_value=completed) as mocked:
                usage = runner._subprocess_invoker(task(workspace), config(directory), Path(directory) / "trajectory.json")
            self.assertEqual(usage, (0, '{"result":"done","usage":{"model_calls":3,"cost":0.25}}\nworker log\n', {"model_calls": 3, "cost": 0.25}))
            self.assertEqual(mocked.call_args.kwargs["timeout"], 20)
            payload = json.loads(mocked.call_args.kwargs["input"])
            self.assertEqual(payload["max_cost"], "1")
            self.assertEqual(payload["wall_time_seconds"], 10)

    def test_timeout_preserves_partial_output_and_trajectory(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            workspace.mkdir()
            artifact_root = Path(directory) / "artifacts"
            trajectory = artifact_root / "task-1" / "attempt-1" / "trajectory.json"

            def timed_out_invoker(run_task, run_config, trajectory_path):
                trajectory_path.write_text('{"partial":true}', encoding="utf-8")
                raise subprocess.TimeoutExpired(
                    cmd="worker", timeout=20, output=b"partial stdout\n", stderr=b"partial stderr\n"
                )

            result = MiniSweAgentHeadlessRunner(timed_out_invoker).run(task(workspace), config(artifact_root))
            self.assertEqual(result.failure_category, RunnerFailureCategory.TIMEOUT)
            self.assertTrue(Path(result.log_path).exists())
            self.assertEqual(Path(result.log_path).read_text(encoding="utf-8"), "partial stdout\npartial stderr\n")
            self.assertEqual(Path(result.trajectory_path).read_text(encoding="utf-8"), '{"partial":true}')

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
            self.assertTrue(Path(result.artifact_path).exists())
            persisted = json.loads(Path(result.artifact_path).read_text(encoding="utf-8"))
            self.assertEqual(persisted, result.to_dict())
            self.assertEqual(result.model_usage, {"calls": 1})
            self.assertEqual(result.treatment, "A")

    def test_run_identity_changes_when_frozen_model_configuration_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            first = config(directory, model="model-a")
            second = config(directory, model="model-b")
            self.assertNotEqual(first.identity_digest(), second.identity_digest())

            runner = MiniSweAgentHeadlessRunner(lambda *_: (0, "", None))
            first_result = runner.run(task(directory), first, attempt=1)
            second_result = runner.run(task(directory), second, attempt=2)
            self.assertNotEqual(first_result.run_id, second_result.run_id)

    def test_run_identity_changes_when_environment_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            first = config(directory, environment="local")
            second = config(directory, environment="git-bash", bash_executable=r"C:\Program Files\Git\bin\bash.exe")
            self.assertNotEqual(first.identity_digest(), second.identity_digest())

    def test_runner_persists_common_manifest_with_distinct_trial_and_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            result = MiniSweAgentHeadlessRunner(lambda *_: (0, "", None)).run(task(directory), config(directory))
            self.assertTrue(Path(result.manifest_path).exists())
            manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
            self.assertEqual(manifest["trial_id"], result.trial_id)
            self.assertEqual(manifest["attempt_id"], result.attempt_id)
            self.assertNotEqual(manifest["trial_id"], manifest["attempt_id"])
            restored = RunManifest.from_dict(manifest)
            restored.validate_attempt_identity()
            restored.validate_lifecycle()
            self.assertTrue(all(Path(reference).exists() for reference in manifest["artifact_refs"]))
            snapshot = load_attempt(Path(result.manifest_path).parent)
            self.assertEqual(snapshot.manifest.attempt_id, result.attempt_id)
            self.assertEqual(manifest["state_history"], ["PLANNED", "STARTED", "EXECUTING", "COMPLETED"])
            self.assertEqual(manifest["artifacts"][0]["status"], "PRESENT")

    def test_missing_identity_is_preserved_in_common_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            result = MiniSweAgentHeadlessRunner().run(task(directory), config(directory, model=None))
            manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
            self.assertEqual(manifest["state"], "BLOCKED")
            self.assertIsNone(manifest["model"])
            self.assertEqual(manifest["errors"][0]["domain"], "HARNESS")
            self.assertEqual(manifest["state_history"], ["PLANNED", "STARTED", "BLOCKED"])
            self.assertEqual(manifest["artifacts"][1]["status"], "MISSING")
            RunManifest.from_dict(manifest).validate_lifecycle()

    def test_subprocess_invoker_passes_explicit_git_bash_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "workspace"
            workspace.mkdir()
            runner = MiniSweAgentHeadlessRunner()
            completed = type("Completed", (), {"returncode": 0, "stdout": "{}\n", "stderr": ""})()
            run_config = config(
                directory,
                environment="git-bash",
                bash_executable=r"C:\Program Files\Git\bin\bash.exe",
            )
            with patch("arkx.p82_baseline.subprocess.run", return_value=completed) as mocked:
                runner._subprocess_invoker(task(workspace), run_config, Path(directory) / "trajectory.json")
            payload = json.loads(mocked.call_args.kwargs["input"])
            self.assertEqual(payload["environment"], "git-bash")
            self.assertEqual(payload["bash_executable"], r"C:\Program Files\Git\bin\bash.exe")

    def test_provider_availability_exit_is_blocked_not_agent_failed(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = MiniSweAgentHeadlessRunner(lambda *_: (75, '{"provider_error":{"code":503}}', {"model_calls": 3}))
            result = runner.run(task(directory), config(directory))
            self.assertEqual(result.state, BaselineExecutionState.BLOCKED)
            self.assertEqual(result.failure_category, RunnerFailureCategory.PROVIDER_AVAILABILITY_FAILURE)
            self.assertEqual(result.error.domain.value, "PROVIDER")
            self.assertEqual(result.error.retryability.value, "RETRYABLE")

    def test_missing_model_or_provider_is_blocked_without_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            result = MiniSweAgentHeadlessRunner().run(task(directory), config(directory, model=None))
            self.assertEqual(result.state, BaselineExecutionState.BLOCKED)
            self.assertIn("model", result.failure)
            self.assertEqual(result.error.domain.value, "HARNESS")

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

    def test_headless_failure_is_classified_without_becoming_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            def failing_invoker(*_):
                raise ValueError("model configuration is invalid")
            result = MiniSweAgentHeadlessRunner(failing_invoker).run(task(directory), config(directory))
            self.assertEqual(result.failure_category, RunnerFailureCategory.MODEL_INITIALIZATION_FAILURE)
            self.assertEqual(result.state, BaselineExecutionState.EXECUTOR_FAILED)
            self.assertEqual(result.error.domain.value, "EXECUTOR")
            self.assertEqual(result.error.code, "EXECUTOR_PROCESS_UNKNOWN")
            self.assertEqual(result.error.retryability.value, "UNKNOWN")

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

    def test_baseline_executor_adapter_returns_neutral_execution_result(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = P82BaselineExecutorAdapter(
                task(directory),
                config(directory),
                MiniSweAgentHeadlessRunner(lambda *_: (0, "log", None)),
            )
            request = ExecutionRequest("task-1", "abc123", "A", "prompt", adapter.executor_id, "test-provider", "test-model", "local", "budget", "config")
            result = adapter.execute(request)
            self.assertEqual(result.state, RunState.COMPLETED)
            self.assertIn("execution.json", " ".join(result.artifact_refs))

    def test_baseline_executor_adapter_preflight_is_read_only_and_identity_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = P82BaselineExecutorAdapter(task(directory), config(directory))
            preflight = adapter.preflight()
            self.assertEqual(preflight.identity.name, adapter.executor_id)
            self.assertEqual(preflight.identity.configuration_digest, adapter.config.identity_digest())
            self.assertEqual(preflight.capabilities, ("edit",))
            self.assertEqual(preflight.capability_provenance.value, "DECLARED")
            self.assertEqual(adapter.config.identity_digest(), adapter.config.configuration_snapshot().digest())
            self.assertNotIn("secret-value", adapter.config.configuration_snapshot().to_json())

    def test_baseline_executor_adapter_rejects_wrong_task(self):
        with tempfile.TemporaryDirectory() as directory:
            adapter = P82BaselineExecutorAdapter(task(directory), config(directory), MiniSweAgentHeadlessRunner(lambda *_: (0, "", None)))
            request = ExecutionRequest("other-task", "abc123", "A", "prompt", adapter.executor_id, "p", "m", "local", "b", "c")
            with self.assertRaises(ValueError):
                adapter.execute(request)


if __name__ == "__main__":
    unittest.main()
