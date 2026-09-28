"""Executor qualification contracts for P8.1.

This module records externally supplied executor observations. It does not
execute an executor, select one, accept a result, or promote a component.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
import json
from statistics import median
from typing import Any

from .composition import Treatment


SCHEMA_VERSION = 1


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class ExecutionOutcome(_ValueEnum):
    COMPLETED = "COMPLETED"
    EXECUTOR_FAILED = "EXECUTOR_FAILED"
    INFRASTRUCTURE_FAILED = "INFRASTRUCTURE_FAILED"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class QualificationStatus(_ValueEnum):
    QUALIFIABLE = "QUALIFIABLE"
    INCOMPARABLE = "INCOMPARABLE"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class ComparisonAxis(_ValueEnum):
    EXECUTOR = "EXECUTOR"
    TREATMENT = "TREATMENT"


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


def _json(value: dict[str, Any]) -> str:
    return json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _nonnegative(value: int | Decimal | None, field_name: str) -> None:
    if value is not None and value < 0:
        raise ValueError(f"{field_name} must be non-negative when present")


def _sorted_refs(refs: tuple[str, ...] | None) -> list[str] | None:
    return None if refs is None else sorted(set(refs))


@dataclass(frozen=True)
class ExecutorIdentity:
    name: str
    version: str | None
    integration_kind: str
    configuration_digest: str | None
    advertised_capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name or not self.integration_kind:
            raise ValueError("Executor name and integration kind must be non-empty")
        capabilities = tuple(self.advertised_capabilities)
        if any(not capability for capability in capabilities):
            raise ValueError("Advertised capability names must be non-empty")
        object.__setattr__(self, "advertised_capabilities", tuple(sorted(set(capabilities))))

    def to_dict(self) -> dict[str, str | None]:
        return {
            "name": self.name,
            "version": self.version,
            "integration_kind": self.integration_kind,
            "configuration_digest": self.configuration_digest,
            "advertised_capabilities": list(self.advertised_capabilities),
        }

    def to_json(self) -> str:
        return _json(self.to_dict())


@dataclass(frozen=True)
class ExecutionEnvironment:
    repository_revision: str | None
    runtime: str | None
    platform: str | None
    toolchain: str | None
    environment_digest: str | None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "repository_revision": self.repository_revision,
            "runtime": self.runtime,
            "platform": self.platform,
            "toolchain": self.toolchain,
            "environment_digest": self.environment_digest,
        }


@dataclass(frozen=True)
class ExecutionBudget:
    max_tokens: int | None
    max_cost: Decimal | None
    max_wall_time: Decimal | None
    max_attempts: int | None
    max_executor_invocations: int | None

    def __post_init__(self) -> None:
        for name in ("max_tokens", "max_attempts", "max_executor_invocations"):
            _nonnegative(getattr(self, name), name)
        _nonnegative(self.max_cost, "max_cost")
        _nonnegative(self.max_wall_time, "max_wall_time")

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_tokens": self.max_tokens,
            "max_cost": self.max_cost,
            "max_wall_time": self.max_wall_time,
            "max_attempts": self.max_attempts,
            "max_executor_invocations": self.max_executor_invocations,
        }


@dataclass(frozen=True)
class QualificationTask:
    task_id: str
    task_revision: str | None
    acceptance_definition: str | None

    def __post_init__(self) -> None:
        if not self.task_id:
            raise ValueError("task_id must be non-empty")

    def to_dict(self) -> dict[str, str | None]:
        return {
            "task_id": self.task_id,
            "task_revision": self.task_revision,
            "acceptance_definition": self.acceptance_definition,
        }


@dataclass(frozen=True)
class ExecutorObservation:
    accepted: bool | None = None
    patch_verified: bool | None = None
    false_pass: bool | None = None
    human_interventions: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    cost: Decimal | None = None
    wall_time_seconds: Decimal | None = None
    attempts: int | None = None
    retries: int | None = None
    replans: int | None = None
    handoffs: int | None = None
    executor_invocations: int | None = None
    unnecessary_changes: int | None = None
    regressions: int | None = None
    error_propagation_observed: bool | None = None
    external_evidence: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "human_interventions", "input_tokens", "output_tokens", "total_tokens",
            "attempts", "retries", "replans", "handoffs", "executor_invocations",
            "unnecessary_changes", "regressions",
        ):
            _nonnegative(getattr(self, field_name), field_name)
        _nonnegative(self.cost, "cost")
        _nonnegative(self.wall_time_seconds, "wall_time_seconds")

    def is_consistent(self) -> bool:
        return not (self.false_pass is True and (self.accepted is not True or self.patch_verified is not False))

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "patch_verified": self.patch_verified,
            "false_pass": self.false_pass,
            "human_interventions": self.human_interventions,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost": self.cost,
            "wall_time_seconds": self.wall_time_seconds,
            "attempts": self.attempts,
            "retries": self.retries,
            "replans": self.replans,
            "handoffs": self.handoffs,
            "executor_invocations": self.executor_invocations,
            "unnecessary_changes": self.unnecessary_changes,
            "regressions": self.regressions,
            "error_propagation_observed": self.error_propagation_observed,
            "external_evidence": _sorted_refs(self.external_evidence),
        }


@dataclass(frozen=True)
class ExecutorTrial:
    executor: ExecutorIdentity
    task: QualificationTask
    model: str | None
    environment: ExecutionEnvironment
    budget: ExecutionBudget
    treatment: Treatment
    replicate_id: str
    outcome: ExecutionOutcome
    observation: ExecutorObservation
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.replicate_id:
            raise ValueError("replicate_id must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "executor": self.executor.to_dict(),
            "task": self.task.to_dict(),
            "model": self.model,
            "environment": self.environment.to_dict(),
            "budget": self.budget.to_dict(),
            "treatment": self.treatment.to_dict(),
            "replicate_id": self.replicate_id,
            "outcome": self.outcome.value,
            "observation": self.observation.to_dict(),
        }

    def to_json(self) -> str:
        return _json(self.to_dict())


@dataclass(frozen=True)
class QualificationExperiment:
    trials: tuple[ExecutorTrial, ...]
    comparison_axis: ComparisonAxis
    schema_version: int = SCHEMA_VERSION
    verifier_identity: str | None = None
    instrumentation_identity: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "comparison_axis": self.comparison_axis.value,
            "verifier_identity": self.verifier_identity,
            "instrumentation_identity": self.instrumentation_identity,
            "trials": [trial.to_dict() for trial in sorted(self.trials, key=lambda item: (item.replicate_id, item.executor.name, item.treatment.name))],
        }

    def to_json(self) -> str:
        return _json(self.to_dict())


@dataclass(frozen=True)
class PairedQualificationReport:
    status: QualificationStatus
    executor_names: tuple[str, ...]
    task_count: int
    replicate_count: int
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "executor_names": list(self.executor_names),
            "task_count": self.task_count,
            "replicate_count": self.replicate_count,
            "reason_codes": list(self.reason_codes),
        }

    def to_json(self) -> str:
        return _json(self.to_dict())


@dataclass(frozen=True)
class QualificationSummary:
    trial_count: int
    qualifiable_trial_count: int
    status_counts: tuple[tuple[str, int], ...]
    outcome_counts: tuple[tuple[str, int], ...]
    acceptance_rate: Decimal | None
    false_pass_rate: Decimal | None
    median_cost: Decimal | None
    median_wall_time_seconds: Decimal | None
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "trial_count": self.trial_count,
            "qualifiable_trial_count": self.qualifiable_trial_count,
            "status_counts": dict(self.status_counts),
            "outcome_counts": dict(self.outcome_counts),
            "acceptance_rate": self.acceptance_rate,
            "false_pass_rate": self.false_pass_rate,
            "median_cost": self.median_cost,
            "median_wall_time_seconds": self.median_wall_time_seconds,
        }

    def to_json(self) -> str:
        return _json(self.to_dict())


def assess_trial(trial: ExecutorTrial) -> QualificationStatus:
    if not _identity_is_complete(trial):
        return QualificationStatus.UNKNOWN
    if not trial.observation.is_consistent():
        return QualificationStatus.BLOCKED
    if trial.outcome is ExecutionOutcome.UNKNOWN:
        return QualificationStatus.UNKNOWN
    if trial.outcome is not ExecutionOutcome.COMPLETED:
        return QualificationStatus.BLOCKED
    if trial.observation.accepted is None:
        return QualificationStatus.UNKNOWN
    return QualificationStatus.QUALIFIABLE


def _identity_is_complete(trial: ExecutorTrial) -> bool:
    """Require the control identity before treating a trial as qualifiable."""

    executor = trial.executor
    task = trial.task
    environment = trial.environment
    return all(
        value is not None and value != ""
        for value in (
            executor.version,
            executor.configuration_digest,
            task.task_revision,
            task.acceptance_definition,
            trial.model,
            environment.repository_revision,
            environment.runtime,
            environment.platform,
            environment.toolchain,
            environment.environment_digest,
        )
    )


def compare_trials(left: ExecutorTrial, right: ExecutorTrial, axis: ComparisonAxis) -> QualificationStatus:
    if left.task != right.task or left.model != right.model or left.environment != right.environment or left.budget != right.budget or left.treatment != right.treatment and axis is ComparisonAxis.EXECUTOR:
        return QualificationStatus.INCOMPARABLE
    if axis is ComparisonAxis.EXECUTOR:
        return QualificationStatus.INCOMPARABLE if left.executor == right.executor else _pair_status(left, right)
    if left.executor != right.executor:
        return QualificationStatus.INCOMPARABLE
    return QualificationStatus.INCOMPARABLE if left.treatment == right.treatment else _pair_status(left, right)


def validate_paired_executor_experiment(experiment: QualificationExperiment) -> PairedQualificationReport:
    """Validate the structural controls for an executor-only paired run.

    This function never ranks executors and never infers a performance result.
    It only decides whether the submitted observations form a comparable pair
    set for a later analysis.
    """
    trials = tuple(experiment.trials)
    executors = tuple(sorted({trial.executor.name for trial in trials}))
    reasons: list[str] = []
    if experiment.comparison_axis is not ComparisonAxis.EXECUTOR:
        reasons.append("COMPARISON_AXIS_NOT_EXECUTOR")
    if len(executors) < 2:
        reasons.append("AT_LEAST_TWO_EXECUTORS_REQUIRED")
    if not experiment.verifier_identity:
        reasons.append("VERIFIER_IDENTITY_MISSING")
    if not experiment.instrumentation_identity:
        reasons.append("INSTRUMENTATION_IDENTITY_MISSING")
    cells: dict[tuple[str, str | None, str | None, str], list[ExecutorTrial]] = {}
    for trial in trials:
        key = (trial.task.task_id, trial.task.task_revision, trial.task.acceptance_definition, trial.replicate_id)
        cells.setdefault(key, []).append(trial)
    if any(len(cell) != len(executors) for cell in cells.values()):
        reasons.append("PAIRED_CELL_INCOMPLETE")
    if any(len({trial.executor.name for trial in cell}) != len(cell) for cell in cells.values()):
        reasons.append("DUPLICATE_EXECUTOR_CELL")
    for cell in cells.values():
        first = cell[0]
        for other in cell[1:]:
            if compare_trials(first, other, ComparisonAxis.EXECUTOR) is QualificationStatus.INCOMPARABLE:
                reasons.append("CONTROL_DIMENSION_MISMATCH")
                break
    if any(not _identity_is_complete(trial) for trial in trials):
        reasons.append("IDENTITY_INCOMPLETE")
    if any(assess_trial(trial) is QualificationStatus.BLOCKED for trial in trials):
        reasons.append("OBSERVED_BLOCKED_TRIAL")
    elif any(assess_trial(trial) is QualificationStatus.UNKNOWN for trial in trials):
        reasons.append("OBSERVATION_INCOMPLETE")
    status = QualificationStatus.QUALIFIABLE if not reasons else (
        QualificationStatus.BLOCKED if "OBSERVED_BLOCKED_TRIAL" in reasons else QualificationStatus.UNKNOWN
    )
    if any(reason in reasons for reason in ("COMPARISON_AXIS_NOT_EXECUTOR", "AT_LEAST_TWO_EXECUTORS_REQUIRED", "PAIRED_CELL_INCOMPLETE", "DUPLICATE_EXECUTOR_CELL", "CONTROL_DIMENSION_MISMATCH")):
        status = QualificationStatus.INCOMPARABLE
    return PairedQualificationReport(status, executors, len({key[:3] for key in cells}), len({key[3] for key in cells}), tuple(sorted(set(reasons))))


def _pair_status(left: ExecutorTrial, right: ExecutorTrial) -> QualificationStatus:
    statuses = (assess_trial(left), assess_trial(right))
    if QualificationStatus.BLOCKED in statuses:
        return QualificationStatus.BLOCKED
    if QualificationStatus.UNKNOWN in statuses:
        return QualificationStatus.UNKNOWN
    return QualificationStatus.QUALIFIABLE


def summarize_experiment(experiment: QualificationExperiment) -> QualificationSummary:
    trials = tuple(experiment.trials)
    statuses = [assess_trial(trial) for trial in trials]
    qualifiable = [trial for trial, status in zip(trials, statuses) if status is QualificationStatus.QUALIFIABLE]
    accepted = [trial.observation.accepted for trial in qualifiable]
    false_pass_values = [trial.observation.false_pass for trial in trials if trial.observation.false_pass is not None]
    costs = [trial.observation.cost for trial in qualifiable if trial.observation.cost is not None]
    wall_times = [trial.observation.wall_time_seconds for trial in qualifiable if trial.observation.wall_time_seconds is not None]
    return QualificationSummary(
        trial_count=len(trials),
        qualifiable_trial_count=len(qualifiable),
        status_counts=tuple(sorted((status.value, statuses.count(status)) for status in set(statuses))),
        outcome_counts=tuple(sorted((outcome.value, sum(trial.outcome is outcome for trial in trials)) for outcome in set(trial.outcome for trial in trials))),
        acceptance_rate=None if not accepted else Decimal(sum(accepted)) / Decimal(len(accepted)),
        false_pass_rate=None if not false_pass_values else Decimal(sum(false_pass_values)) / Decimal(len(false_pass_values)),
        median_cost=None if not costs else median(costs),
        median_wall_time_seconds=None if not wall_times else median(wall_times),
    )
