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
import json
from pathlib import Path
import os
import subprocess
from typing import Any, Callable, Protocol

from .p82 import P82Observation, P82RunStatus, P82Treatment, TaskStratum


PROTOCOL_VERSION = "p8.2a-v1"


class VerificationState(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INDETERMINATE = "INDETERMINATE"
    NOT_EXECUTED = "NOT_EXECUTED"
    BLOCKED = "BLOCKED"


class AcceptanceDecision(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    INDETERMINATE = "INDETERMINATE"
    NOT_EXECUTED = "NOT_EXECUTED"
    BLOCKED = "BLOCKED"


class BaselineExecutionState(str, Enum):
    COMPLETED = "COMPLETED"
    EXECUTOR_FAILED = "EXECUTOR_FAILED"
    BLOCKED = "BLOCKED"


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
    treatment: P82Treatment = P82Treatment.A

    def __post_init__(self) -> None:
        if self.treatment is not P82Treatment.A:
            raise ValueError("P8.2a baseline runner accepts treatment A only")
        for name in ("max_tokens", "wall_time_seconds"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative when present")

    def missing_identity(self) -> tuple[str, ...]:
        return tuple(name for name in ("provider", "model", "mini_version", "python_executable") if getattr(self, name) is None)


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
    diff_path: str | None
    log_path: str | None
    trajectory_path: str | None
    model_usage: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in (
            "run_id", "state", "task_id", "treatment", "attempt", "started_at", "finished_at",
            "exit_code", "failure", "diff_path", "log_path", "trajectory_path", "model_usage")}


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
        root = Path(config.artifact_root) / task.task_id / f"attempt-{attempt}"
        run_id = hashlib.sha256(f"{task.task_id}|A|{attempt}|{config.runner_version}".encode()).hexdigest()[:16]
        if root.exists():
            return self._blocked(run_id, task, attempt, "artifact already exists; refusing silent overwrite")
        root.mkdir(parents=True)
        started = _now()
        trajectory = root / "trajectory.json"
        if missing:
            return self._finish(root, run_id, task, attempt, started, BaselineExecutionState.BLOCKED, None,
                                f"missing explicit identity: {','.join(missing)}", None, None, None, None)
        try:
            exit_code, log, usage = self.invoker(task, config, trajectory)
            log_path = root / "executor.log"
            log_path.write_text(log, encoding="utf-8")
            diff_path = root / "diff.patch"
            diff = subprocess.run(["git", "diff", "--binary"], cwd=task.workspace, capture_output=True, text=True, check=False)
            diff_path.write_text(diff.stdout, encoding="utf-8")
            state = BaselineExecutionState.COMPLETED if exit_code == 0 else BaselineExecutionState.EXECUTOR_FAILED
            return self._finish(root, run_id, task, attempt, started, state, exit_code, None if exit_code == 0 else "executor returned non-zero", str(diff_path), str(log_path), str(trajectory), usage)
        except Exception as error:
            return self._finish(root, run_id, task, attempt, started, BaselineExecutionState.EXECUTOR_FAILED, None, f"{type(error).__name__}: {error}", None, None, None)

    def _subprocess_invoker(self, task: ProspectiveTask, config: BaselineRunConfig, trajectory_path: Path) -> tuple[int, str, dict[str, Any] | None]:
        worker = Path(__file__).parents[2] / "tools" / "run_mini_headless.py"
        payload = {"task": task.problem_statement, "workspace": task.workspace, "model": config.model,
                   "trajectory": str(trajectory_path), "max_cost": config.max_cost, "wall_time_seconds": config.wall_time_seconds,
                   "model_configuration": config.model_configuration}
        completed = subprocess.run([config.python_executable, str(worker)], input=json.dumps(payload), text=True,
                                   capture_output=True, cwd=task.workspace, timeout=config.wall_time_seconds)
        return completed.returncode, completed.stdout + completed.stderr, None

    def _blocked(self, run_id: str, task: ProspectiveTask, attempt: int, failure: str) -> ExecutionArtifact:
        now = _now()
        return ExecutionArtifact(run_id, BaselineExecutionState.BLOCKED, task.task_id, "A", attempt, now, now, None, failure, None, None, None, None)

    def _finish(self, root: Path, run_id: str, task: ProspectiveTask, attempt: int, started: str, state: BaselineExecutionState, exit_code: int | None, failure: str | None, diff_path: str | None, log_path: str | None, trajectory_path: str | None, usage: dict[str, Any] | None) -> ExecutionArtifact:
        return ExecutionArtifact(run_id, state, task.task_id, "A", attempt, started, _now(), exit_code, failure, diff_path, log_path, trajectory_path, usage)


@dataclass(frozen=True)
class VerificationResult:
    state: VerificationState
    authority: str
    commands: tuple[str, ...]
    outcomes: tuple[str, ...]
    evidence: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"state": self.state.value, "authority": self.authority, "commands": list(self.commands), "outcomes": list(self.outcomes), "evidence": list(self.evidence)}


@dataclass(frozen=True)
class AcceptanceResult:
    decision: AcceptanceDecision
    authority: str
    raw_outcome: str | None
    evidence: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"decision": self.decision.value, "authority": self.authority, "raw_outcome": self.raw_outcome, "evidence": list(self.evidence)}


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
