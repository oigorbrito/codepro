"""P8.2a baseline execution path.

This is infrastructure qualification, not mechanism evidence. The runner
captures executor output only; verification and independent acceptance are
separate contracts and are never inferred from an exit status or a diff.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import importlib.util
import json
from pathlib import Path
import os
import subprocess
from typing import Any, Callable, Protocol

from .outcomes import AcceptanceDecision, AcceptanceResult, VerificationResult, VerificationState
from .harness import ArtifactRecord, ArtifactStatus, ArtifactStore, ErrorDomain, ErrorEnvelope, LifecycleEvent, Retryability, RunManifest, RunState, derive_attempt_id, validate_execution_artifact_consistency
from .execution import ExecutionRequest, ExecutionResult
from .configuration import ConfigurationSnapshot
from .integration import IntegrationKind, process_error_envelope
from .integration import AdapterIdentity, DependencyObservation, CapabilityProvenance, assess_preflight, AdapterPreflight
from .p82 import P82Observation, P82RunStatus, P82Treatment, TaskStratum
from .submission import SubmissionArtifact
from .timeouts import TimeoutObservation, TimeoutOrigin


PROTOCOL_VERSION = "p8.2a-v1"


class BaselineExecutionState(str, Enum):
    COMPLETED = "COMPLETED"
    EXECUTOR_FAILED = "EXECUTOR_FAILED"
    BLOCKED = "BLOCKED"


class RunnerFailureCategory(str, Enum):
    PROCESS_START_FAILURE = "PROCESS_START_FAILURE"
    ENVIRONMENT_FAILURE = "ENVIRONMENT_FAILURE"
    MODEL_INITIALIZATION_FAILURE = "MODEL_INITIALIZATION_FAILURE"
    AGENT_INITIALIZATION_FAILURE = "AGENT_INITIALIZATION_FAILURE"
    AGENT_RUN_FAILURE = "AGENT_RUN_FAILURE"
    TIMEOUT = "TIMEOUT"
    DEADLOCK_HANG = "DEADLOCK/HANG"
    OUTPUT_CAPTURE_FAILURE = "OUTPUT_CAPTURE_FAILURE"
    PROVIDER_AVAILABILITY_FAILURE = "PROVIDER_AVAILABILITY_FAILURE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ProspectiveTask:
    task_id: str
    source_dataset: str | None
    repository: str | None
    base_commit: str | None
    problem_statement: str | None
    stratum: TaskStratum
    rationale: str | None
    selection_timestamp: str | None
    protocol_version: str | None
    verification_identity: str | None
    acceptance_authority_identity: str | None
    workspace: str

    def __post_init__(self) -> None:
        if not self.task_id or not self.workspace:
            raise ValueError("task_id and workspace must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        value = {name: getattr(self, name) for name in (
            "task_id", "source_dataset", "repository", "base_commit", "problem_statement",
            "stratum", "rationale", "selection_timestamp", "protocol_version",
            "verification_identity", "acceptance_authority_identity", "workspace")}
        value["stratum"] = self.stratum.value
        return value


@dataclass(frozen=True)
class BaselineSampleManifest:
    sample_id: str
    wave: str
    selection_rule: str
    tasks: tuple[ProspectiveTask, ...]
    protocol_version: str = PROTOCOL_VERSION

    def __post_init__(self) -> None:
        if not self.sample_id or not self.wave or not self.selection_rule:
            raise ValueError("sample identity, wave, and selection rule are required")
        if not self.tasks:
            raise ValueError("prospective sample cannot be empty")
        if len({task.task_id for task in self.tasks}) != len(self.tasks):
            raise ValueError("sample task identifiers must be unique")
        object.__setattr__(self, "tasks", tuple(sorted(self.tasks, key=lambda task: task.task_id)))

    def to_dict(self) -> dict[str, Any]:
        return {"sample_id": self.sample_id, "wave": self.wave, "selection_rule": self.selection_rule,
                "protocol_version": self.protocol_version, "tasks": [task.to_dict() for task in self.tasks]}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class BaselineRunConfig:
    provider: str | None
    model: str | None
    model_version: str | None
    temperature: str | None
    reasoning_configuration: str | None
    model_configuration: dict[str, Any] | None
    max_tokens: int | None
    max_cost: str | None
    wall_time_seconds: int | None
    mini_version: str | None
    python_executable: str | None
    runner_version: str
    artifact_root: str
    model_class: str | None = None
    treatment: P82Treatment = P82Treatment.A
    environment: str = "local"
    bash_executable: str | None = None
    environment_configuration: dict[str, Any] | None = None
    provider_retry_attempts: int = 0
    provider_retry_backoff_seconds: float = 0.0
    agent_step_limit: int | None = None

    def __post_init__(self) -> None:
        if self.treatment is not P82Treatment.A:
            raise ValueError("P8.2a baseline runner accepts treatment A only")
        for name in ("max_tokens", "wall_time_seconds"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative when present")
        if self.provider_retry_attempts < 0 or self.provider_retry_backoff_seconds < 0:
            raise ValueError("provider retry limits must be non-negative")

    def missing_identity(self) -> tuple[str, ...]:
        return tuple(name for name in ("provider", "model", "mini_version", "python_executable") if getattr(self, name) is None)

    def identity_digest(self) -> str:
        """Return a stable digest for the frozen execution configuration."""
        return self.configuration_snapshot().digest()

    def configuration_snapshot(self) -> ConfigurationSnapshot:
        """Return the canonical, secret-safe configuration identity."""
        value = {
            "provider": self.provider,
            "model": self.model,
            "model_version": self.model_version,
            "temperature": self.temperature,
            "reasoning_configuration": self.reasoning_configuration,
            "model_configuration": self.model_configuration,
            "max_tokens": self.max_tokens,
            "max_cost": self.max_cost,
            "wall_time_seconds": self.wall_time_seconds,
            "mini_version": self.mini_version,
            "python_executable": self.python_executable,
            "model_class": self.model_class,
            "runner_version": self.runner_version,
            "treatment": self.treatment.value,
            "environment": self.environment,
            "bash_executable": self.bash_executable,
            "environment_configuration": self.environment_configuration,
            "provider_retry_attempts": self.provider_retry_attempts,
            "provider_retry_backoff_seconds": self.provider_retry_backoff_seconds,
            "agent_step_limit": self.agent_step_limit,
        }
        return ConfigurationSnapshot("p82-baseline-executor", self.runner_version, value)

    def budget_digest(self) -> str:
        value = {
            "max_tokens": self.max_tokens,
            "max_cost": self.max_cost,
            "wall_time_seconds": self.wall_time_seconds,
            "provider_retry_attempts": self.provider_retry_attempts,
            "provider_retry_backoff_seconds": self.provider_retry_backoff_seconds,
        }
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class ExecutionArtifact:
    run_id: str
    state: BaselineExecutionState
    task_id: str
    treatment: str
    attempt: int
    started_at: str
    finished_at: str
    exit_code: int | None
    failure: str | None
    failure_category: RunnerFailureCategory | None
    diff_path: str | None
    log_path: str | None
    trajectory_path: str | None
    model_usage: dict[str, Any] | None
    artifact_path: str | None = None
    trial_id: str | None = None
    attempt_id: str | None = None
    manifest_path: str | None = None
    error: ErrorEnvelope | None = None
    submission_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = {name: getattr(self, name) for name in (
            "run_id", "state", "task_id", "treatment", "attempt", "started_at", "finished_at",
            "exit_code", "failure", "failure_category", "diff_path", "log_path", "trajectory_path",
            "model_usage", "artifact_path", "trial_id", "attempt_id", "manifest_path", "error")}
        value["submission_path"] = self.submission_path
        if isinstance(value.get("error"), ErrorEnvelope):
            value["error"] = value["error"].to_dict()
        for name in ("state", "failure_category"):
            if isinstance(value[name], Enum):
                value[name] = value[name].value
        return value

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class HeadlessInvoker(Protocol):
    def __call__(self, task: ProspectiveTask, config: BaselineRunConfig, trajectory_path: Path) -> tuple[int, str, dict[str, Any] | None]: ...


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class MiniSweAgentHeadlessRunner:
    """Narrow runner. It never calls verification or acceptance."""

    def __init__(self, invoker: HeadlessInvoker | None = None) -> None:
        self.invoker = invoker or self._subprocess_invoker

    def run(self, task: ProspectiveTask, config: BaselineRunConfig, attempt: int = 1) -> ExecutionArtifact:
        if attempt < 1:
            raise ValueError("attempt must be positive")
        missing = config.missing_identity()
        store = ArtifactStore(config.artifact_root)
        trial_id = hashlib.sha256(
            f"{task.task_id}|{task.base_commit}|A|{config.identity_digest()}".encode("utf-8")
        ).hexdigest()[:16]
        run_id = derive_attempt_id(
            trial_id=trial_id,
            attempt_number=attempt,
            configuration_digest=config.identity_digest(),
        )
        try:
            root = store.reserve_attempt(task.task_id, attempt)
        except FileExistsError:
            return self._blocked(run_id, task, attempt, "artifact already exists; refusing silent overwrite")
        started = _now()
        trajectory = root / "trajectory.json"
        if missing:
            return self._finish(root, run_id, trial_id, task, config, attempt, started, False, BaselineExecutionState.BLOCKED, None,
                                f"missing explicit identity: {','.join(missing)}", RunnerFailureCategory.UNKNOWN, None, None, None, None)
        try:
            exit_code, log, usage = self.invoker(task, config, trajectory)
            log_path = root / "executor.log"
            log_path.write_text(log, encoding="utf-8")
            diff_path = root / "diff.patch"
            submission = SubmissionArtifact.from_git_workspace(task.workspace)
            diff_path.write_text(submission.normalized_patch, encoding="utf-8", newline="\n")
            submission_path = root / "submission.json"
            submission_path.write_text(json.dumps(submission.to_dict(), ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
            if exit_code == 75:
                return self._finish(root, run_id, trial_id, task, config, attempt, started, True, BaselineExecutionState.BLOCKED, exit_code,
                                    "provider availability failure after bounded retries",
                                    RunnerFailureCategory.PROVIDER_AVAILABILITY_FAILURE,
                                    str(diff_path), str(log_path), str(trajectory), usage, str(submission_path))
            state = BaselineExecutionState.COMPLETED if exit_code == 0 else BaselineExecutionState.EXECUTOR_FAILED
            return self._finish(root, run_id, trial_id, task, config, attempt, started, True, state, exit_code, None if exit_code == 0 else "executor returned non-zero", None if exit_code == 0 else RunnerFailureCategory.AGENT_RUN_FAILURE, str(diff_path), str(log_path), str(trajectory), usage, str(submission_path))
        except subprocess.TimeoutExpired as error:
            log_path = root / "executor.log"
            stdout = self._decode_process_output(error.stdout)
            stderr = self._decode_process_output(error.stderr)
            log_path.write_text(stdout + stderr, encoding="utf-8", newline="\n")
            diagnostics_path = root / "timeout-observability.json"
            diagnostics_path.write_text(json.dumps({
                "event": "runner_timeout",
                "timeout_origin": "runner_subprocess_watchdog",
                "timeout_seconds": error.timeout,
                "started_at": started,
                "finished_at": _now(),
                "exception_type": type(error).__name__,
                "exception": str(error),
                "model_diagnostics_path": str(root / "model-observability.json"),
                "timeout": TimeoutObservation(TimeoutOrigin.RUNNER_WATCHDOG, error.timeout, "CodePro MiniSweAgentHeadlessRunner", "subprocess.TimeoutExpired").to_dict(),
            }, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
            return self._finish(
                root, run_id, trial_id, task, config, attempt, started, True,
                BaselineExecutionState.EXECUTOR_FAILED, None, str(error),
                RunnerFailureCategory.TIMEOUT, None, str(log_path),
                str(trajectory) if trajectory.exists() else None, None,
            )
        except Exception as error:
            message = f"{type(error).__name__}: {error}"
            return self._finish(root, run_id, trial_id, task, config, attempt, started, True, BaselineExecutionState.EXECUTOR_FAILED, None, message, self._classify_failure(message), None, None, None, None)

    @staticmethod
    def _classify_failure(message: str) -> RunnerFailureCategory:
        lowered = message.lower()
        if "filenotfound" in lowered or "process" in lowered and "start" in lowered:
            return RunnerFailureCategory.PROCESS_START_FAILURE
        if "timeout" in lowered or "timed out" in lowered:
            return RunnerFailureCategory.TIMEOUT
        if "environment" in lowered or "docker" in lowered or "workspace" in lowered:
            return RunnerFailureCategory.ENVIRONMENT_FAILURE
        if "model" in lowered and ("validation" in lowered or "initial" in lowered or "config" in lowered):
            return RunnerFailureCategory.MODEL_INITIALIZATION_FAILURE
        if "agent" in lowered and ("initial" in lowered or "config" in lowered):
            return RunnerFailureCategory.AGENT_INITIALIZATION_FAILURE
        if "trajectory" in lowered or "capture" in lowered:
            return RunnerFailureCategory.OUTPUT_CAPTURE_FAILURE
        if "deadlock" in lowered or "hang" in lowered:
            return RunnerFailureCategory.DEADLOCK_HANG
        return RunnerFailureCategory.AGENT_RUN_FAILURE

    @staticmethod
    def _decode_process_output(value: str | bytes | None) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return value

    def _subprocess_invoker(self, task: ProspectiveTask, config: BaselineRunConfig, trajectory_path: Path) -> tuple[int, str, dict[str, Any] | None]:
        worker = Path(__file__).parents[2] / "tools" / "run_mini_headless.py"
        payload = {"task": task.problem_statement, "workspace": task.workspace, "model": config.model,
                   "model_class": config.model_class,
                   "trajectory": str(trajectory_path), "max_cost": config.max_cost, "wall_time_seconds": config.wall_time_seconds,
                   "model_configuration": config.model_configuration, "environment": config.environment,
                   "bash_executable": config.bash_executable, "provider_retry_attempts": config.provider_retry_attempts,
                   "provider_retry_backoff_seconds": config.provider_retry_backoff_seconds,
                   "agent_step_limit": config.agent_step_limit,
                   "environment_configuration": config.environment_configuration,
                   "diagnostics_path": str(trajectory_path.with_name("model-observability.json").resolve())}
        timeout = None if config.wall_time_seconds is None else config.wall_time_seconds + 10
        completed = subprocess.run(
            [config.python_executable, str(worker)], input=json.dumps(payload), text=True,
            capture_output=True, cwd=task.workspace, timeout=timeout, env=os.environ.copy(),
        )
        combined_log = completed.stdout + completed.stderr
        usage = None
        if completed.returncode == 0:
            lines = [line for line in completed.stdout.splitlines() if line.strip()]
            if lines:
                try:
                    worker_result = json.loads(lines[-1])
                    usage = worker_result.get("usage")
                    result = worker_result.get("result", {})
                    if isinstance(result, dict) and result.get("failure_category") == RunnerFailureCategory.PROVIDER_AVAILABILITY_FAILURE.value:
                        return 75, combined_log, usage
                except (json.JSONDecodeError, AttributeError):
                    usage = None
        return completed.returncode, combined_log, usage

    def _blocked(self, run_id: str, task: ProspectiveTask, attempt: int, failure: str) -> ExecutionArtifact:
        now = _now()
        return ExecutionArtifact(run_id, BaselineExecutionState.BLOCKED, task.task_id, "A", attempt, now, now, None, failure, RunnerFailureCategory.UNKNOWN, None, None, None, None)

    def _finish(self, root: Path, run_id: str, trial_id: str, task: ProspectiveTask, config: BaselineRunConfig, attempt: int, started: str, execution_started: bool, state: BaselineExecutionState, exit_code: int | None, failure: str | None, failure_category: RunnerFailureCategory | None, diff_path: str | None, log_path: str | None, trajectory_path: str | None, usage: dict[str, Any] | None, submission_path: str | None = None) -> ExecutionArtifact:
        store = ArtifactStore(root.parents[1])
        artifact_path = root / "execution.json"
        manifest_path = root / "manifest.json"
        error = None
        if failure:
            raw_refs = tuple(path for path in (log_path, trajectory_path) if path)
            if failure_category is RunnerFailureCategory.PROVIDER_AVAILABILITY_FAILURE:
                # This is the one legacy classification with an explicit retry policy.
                error = ErrorEnvelope(
                    domain=ErrorDomain.PROVIDER,
                    code=failure_category.value,
                    message=failure,
                    retryability=Retryability.RETRYABLE,
                    raw_evidence_refs=raw_refs,
                    attempt_number=attempt,
                )
            elif failure_category is RunnerFailureCategory.UNKNOWN:
                # Missing identity is a harness precondition failure, not an
                # executor invocation failure.
                error = ErrorEnvelope(
                    domain=ErrorDomain.HARNESS,
                    code=RunnerFailureCategory.UNKNOWN.value,
                    message=failure,
                    retryability=Retryability.UNKNOWN,
                    raw_evidence_refs=raw_refs,
                    attempt_number=attempt,
                )
            else:
                kind = IntegrationKind.SANDBOX if failure_category in (
                    RunnerFailureCategory.ENVIRONMENT_FAILURE,
                    RunnerFailureCategory.PROCESS_START_FAILURE,
                ) else IntegrationKind.EXECUTOR
                error = process_error_envelope(
                    kind,
                    returncode=exit_code,
                    message=failure,
                    raw_evidence_refs=raw_refs,
                    attempt_number=attempt,
                )
        manifest = RunManifest(
            experiment_id=f"p82a:{config.runner_version}", trial_id=trial_id, attempt_id=run_id,
            attempt_number=attempt, task_id=task.task_id, task_revision=task.base_commit,
            treatment="A", executor="mini-swe-agent", provider=config.provider,
            model=config.model, sandbox=config.environment, repository_revision=task.base_commit,
            configuration_digest=config.identity_digest(), protocol_version=task.protocol_version or PROTOCOL_VERSION,
            budget_digest=config.budget_digest(),
            state={BaselineExecutionState.COMPLETED: RunState.COMPLETED, BaselineExecutionState.EXECUTOR_FAILED: RunState.FAILED, BaselineExecutionState.BLOCKED: RunState.BLOCKED}[state],
            state_history=(RunState.PLANNED, RunState.STARTED) + ((RunState.EXECUTING,) if execution_started else ()) + ({BaselineExecutionState.COMPLETED: (RunState.COMPLETED,), BaselineExecutionState.EXECUTOR_FAILED: (RunState.FAILED,), BaselineExecutionState.BLOCKED: (RunState.BLOCKED,)}[state]),
            lifecycle_events=tuple(
                LifecycleEvent(current, started if index < 2 else _now())
                for index, current in enumerate((RunState.PLANNED, RunState.STARTED) + ((RunState.EXECUTING,) if execution_started else ()) + ({BaselineExecutionState.COMPLETED: (RunState.COMPLETED,), BaselineExecutionState.EXECUTOR_FAILED: (RunState.FAILED,), BaselineExecutionState.BLOCKED: (RunState.BLOCKED,)}[state]))
            ),
            artifacts=tuple(
                ArtifactRecord(
                    kind=kind,
                    status=ArtifactStatus.PRESENT if path == str(artifact_path) or (path is not None and Path(path).is_file()) else ArtifactStatus.MISSING,
                    path=path if path == str(artifact_path) or (path is not None and Path(path).is_file()) else None,
                    required=kind == "execution",
                    reason=None if path == str(artifact_path) or (path is not None and Path(path).is_file()) else "not produced by this attempt",
                )
                for kind, path in (("execution", str(artifact_path)), ("diff", diff_path), ("submission", submission_path), ("executor_log", log_path), ("trajectory", trajectory_path))
            ),
            artifact_refs=tuple(
                [str(artifact_path)] + [
                    path for path in (diff_path, log_path, trajectory_path)
                    if path and Path(path).is_file()
                ]
            ),
            errors=(error,) if error else (),
        )
        manifest.validate_attempt_identity()
        manifest.validate_lifecycle()
        artifact = ExecutionArtifact(run_id, state, task.task_id, "A", attempt, started, _now(), exit_code, failure, failure_category, diff_path, log_path, trajectory_path, usage, str(artifact_path), trial_id, run_id, str(manifest_path), error, submission_path)
        store.write_text_atomic(manifest_path, manifest.to_json() + "\n")
        store.write_text_atomic(artifact_path, artifact.to_json() + "\n")
        validate_execution_artifact_consistency(manifest, artifact.to_dict())
        store.validate_manifest_references(manifest)
        return artifact

    @staticmethod
    def _error_domain(category: RunnerFailureCategory | None) -> ErrorDomain:
        if category is RunnerFailureCategory.PROVIDER_AVAILABILITY_FAILURE:
            return ErrorDomain.PROVIDER
        if category in (RunnerFailureCategory.ENVIRONMENT_FAILURE, RunnerFailureCategory.PROCESS_START_FAILURE):
            return ErrorDomain.SANDBOX
        if category is RunnerFailureCategory.UNKNOWN or category is None:
            return ErrorDomain.HARNESS
        return ErrorDomain.EXECUTOR


class P82BaselineExecutorAdapter:
    """Translate the legacy P8.2 runner into the neutral Executor contract."""

    executor_id = "p82-baseline-mini-swe-agent"

    def __init__(self, task: ProspectiveTask, config: BaselineRunConfig, runner: MiniSweAgentHeadlessRunner | None = None, attempt: int = 1) -> None:
        self.task = task
        self.config = config
        self.runner = runner or MiniSweAgentHeadlessRunner()
        self.attempt = attempt

    def preflight(self) -> AdapterPreflight:
        """Describe concrete readiness without invoking the runner."""
        available = importlib.util.find_spec("minisweagent") is not None
        return assess_preflight(
            AdapterIdentity(
                IntegrationKind.EXECUTOR,
                self.executor_id,
                self.config.mini_version,
                self.config.configuration_snapshot().digest(),
            ),
            (DependencyObservation("minisweagent", available, reason=None if available else "python module unavailable"),),
            capabilities=("edit",),
            capability_digest=self.config.configuration_snapshot().digest(),
            capability_provenance=CapabilityProvenance.DECLARED,
        )

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        if request.task_id != self.task.task_id:
            raise ValueError("execution request task_id does not match bound baseline task")
        if request.treatment != "A":
            raise ValueError("P8.2 baseline adapter accepts treatment A only")
        artifact = self.runner.run(self.task, self.config, attempt=self.attempt)
        state = {
            BaselineExecutionState.COMPLETED: RunState.COMPLETED,
            BaselineExecutionState.EXECUTOR_FAILED: RunState.FAILED,
            BaselineExecutionState.BLOCKED: RunState.BLOCKED,
        }[artifact.state]
        return ExecutionResult(
            state=state,
            artifact_refs=tuple(ref for ref in (artifact.artifact_path, artifact.diff_path, artifact.submission_path, artifact.log_path, artifact.trajectory_path, artifact.manifest_path) if ref),
            usage=artifact.model_usage,
            error=artifact.error,
        )


class IndependentAcceptanceAuthority(Protocol):
    identity: str

    def decide(self, verification: VerificationResult) -> AcceptanceResult: ...


class ExplicitVerificationAcceptance:
    """An explicit policy: verification PASS maps to acceptance only by declaration."""

    def __init__(self, identity: str) -> None:
        if not identity:
            raise ValueError("acceptance authority identity must be explicit")
        self.identity = identity

    def decide(self, verification: VerificationResult) -> AcceptanceResult:
        mapping = {
            VerificationState.PASS: AcceptanceDecision.ACCEPTED,
            VerificationState.FAIL: AcceptanceDecision.REJECTED,
            VerificationState.INDETERMINATE: AcceptanceDecision.INDETERMINATE,
            VerificationState.NOT_EXECUTED: AcceptanceDecision.NOT_EXECUTED,
            VerificationState.BLOCKED: AcceptanceDecision.BLOCKED,
        }
        return AcceptanceResult(mapping[verification.state], self.identity, verification.state.value, verification.evidence)


def baseline_observation(execution: ExecutionArtifact, verification: VerificationResult | None, acceptance: AcceptanceResult | None) -> P82Observation:
    if execution.state is BaselineExecutionState.BLOCKED:
        status = P82RunStatus.BLOCKED
    elif execution.state is not BaselineExecutionState.COMPLETED:
        status = P82RunStatus.EXECUTED
    else:
        status = P82RunStatus.EXECUTED
    accepted = None if acceptance is None else acceptance.decision is AcceptanceDecision.ACCEPTED
    return P82Observation(status=status, verified_acceptance=accepted)
