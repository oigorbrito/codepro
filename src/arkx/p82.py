"""P8.2 minimal mechanism trial design.

This module defines the controlled A/B/C/D design only. It never invokes an
executor, applies a mechanism, verifies a patch, or makes an acceptance
decision. Results must be recorded later as :class:`ExecutorTrial` records.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
import json
from statistics import median
from typing import Any, Iterable

from .composition import Mechanism, Treatment
from .executor_qualification import (
    ExecutionBudget,
    ExecutionEnvironment,
    ExecutorIdentity,
    QualificationTask,
)


SCHEMA_VERSION = 1


class P82Treatment(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class TaskStratum(str, Enum):
    CHALLENGER_RECOVERY = "challenger_recovery"
    LOCALIZATION_CONTEXT = "localization_context"
    MINI_CONTROL = "mini_control"
    HARD_ALL_FAIL = "hard_all_fail"


class P82RunStatus(str, Enum):
    NOT_EXECUTED = "NOT_EXECUTED"
    BLOCKED = "BLOCKED"
    EXECUTED = "EXECUTED"


class P82Comparability(str, Enum):
    COMPARABLE = "COMPARABLE"
    NOT_COMPARABLE = "NOT_COMPARABLE"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class P82Criteria:
    primary_metrics: tuple[str, ...] = ("verified_acceptance", "cost_to_acceptance")
    secondary_metrics: tuple[str, ...] = (
        "tokens_to_acceptance", "wall_time_seconds", "model_calls", "turns",
        "repeated_exploration", "repeated_file_reads_searches", "edit_failures",
        "retries", "replans", "unnecessary_diff", "regressions", "human_intervention",
    )
    guardrail: str = "false_pass_must_not_increase"

    def to_dict(self) -> dict[str, Any]:
        return {"primary_metrics": list(self.primary_metrics), "secondary_metrics": list(self.secondary_metrics), "guardrail": self.guardrail}

    def to_json(self) -> str:
        return _json(self.to_dict())


def _json(value: Any) -> str:
    return json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "to_dict"):
        return _jsonable(value.to_dict())
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _treatment(name: P82Treatment) -> Treatment:
    mechanisms = {
        P82Treatment.A: (),
        P82Treatment.B: (Mechanism.P8_SAFE_EDITOR,),
        P82Treatment.C: (Mechanism.P8_ENHANCED_REPOSITORY_CONTEXT,),
        P82Treatment.D: (Mechanism.P8_SAFE_EDITOR, Mechanism.P8_ENHANCED_REPOSITORY_CONTEXT),
    }
    return Treatment(name.value, mechanisms[name])


@dataclass(frozen=True)
class P82ExperimentConfig:
    """Frozen controls shared by every planned arm."""

    executor: ExecutorIdentity
    model: str | None
    environment: ExecutionEnvironment
    budget: ExecutionBudget
    tasks: tuple[QualificationTask, ...]
    replicate_ids: tuple[str, ...] = ("rep-1",)
    verification_contract: str | None = None
    acceptance_authority: str | None = None
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        tasks = tuple(self.tasks)
        if not tasks:
            raise ValueError("P8.2 requires at least one task")
        if len({task.task_id for task in tasks}) != len(tasks):
            raise ValueError("P8.2 task identifiers must be unique")
        replicates = tuple(self.replicate_ids)
        if not replicates or any(not replicate for replicate in replicates):
            raise ValueError("P8.2 requires non-empty replicate identifiers")
        if len(set(replicates)) != len(replicates):
            raise ValueError("P8.2 replicate identifiers must be unique")
        object.__setattr__(self, "tasks", tuple(sorted(tasks, key=lambda task: task.task_id)))
        object.__setattr__(self, "replicate_ids", tuple(sorted(replicates)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "executor": self.executor.to_dict(),
            "model": self.model,
            "environment": self.environment.to_dict(),
            "budget": self.budget.to_dict(),
            "tasks": [task.to_dict() for task in self.tasks],
            "replicate_ids": list(self.replicate_ids),
            "verification_contract": self.verification_contract,
            "acceptance_authority": self.acceptance_authority,
        }


@dataclass(frozen=True)
class P82TrialPlan:
    treatment: Treatment
    task: QualificationTask
    replicate_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "treatment": self.treatment.to_dict(),
            "task": self.task.to_dict(),
            "replicate_id": self.replicate_id,
        }


@dataclass(frozen=True)
class P82ExperimentPlan:
    config: P82ExperimentConfig
    treatments: tuple[Treatment, ...]
    trials: tuple[P82TrialPlan, ...]
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "config": self.config.to_dict(),
            "treatments": [treatment.to_dict() for treatment in self.treatments],
            "trials": [trial.to_dict() for trial in self.trials],
        }

    def to_json(self) -> str:
        return _json(self.to_dict())


@dataclass(frozen=True)
class TaskSampleTask:
    task: QualificationTask
    stratum: TaskStratum
    provenance: tuple[str, ...] | None = None
    evidence: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        for name, values in (("provenance", self.provenance), ("evidence", self.evidence)):
            if values is not None and any(not value for value in values):
                raise ValueError(f"{name} references must be non-empty when present")

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task.to_dict(),
            "stratum": self.stratum.value,
            "provenance": None if self.provenance is None else sorted(set(self.provenance)),
            "evidence": None if self.evidence is None else sorted(set(self.evidence)),
        }


@dataclass(frozen=True)
class TaskSampleManifest:
    sample_id: str
    tasks: tuple[TaskSampleTask, ...]
    sample_revision: str | None = None
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.sample_id:
            raise ValueError("sample_id must be non-empty")
        tasks = tuple(sorted(self.tasks, key=lambda item: item.task.task_id))
        if not tasks:
            raise ValueError("task sample must contain at least one task")
        if len({item.task.task_id for item in tasks}) != len(tasks):
            raise ValueError("task sample task identifiers must be unique")
        object.__setattr__(self, "tasks", tasks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "sample_id": self.sample_id,
            "sample_revision": self.sample_revision,
            "tasks": [task.to_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "TaskSampleManifest":
        tasks = tuple(
            TaskSampleTask(
                QualificationTask(**item["task"]),
                TaskStratum(item["stratum"]),
                None if item.get("provenance") is None else tuple(item["provenance"]),
                None if item.get("evidence") is None else tuple(item["evidence"]),
            )
            for item in value["tasks"]
        )
        return cls(value["sample_id"], tasks, value.get("sample_revision"), value.get("schema_version", SCHEMA_VERSION))


@dataclass(frozen=True)
class P82RunManifest:
    """All run identity needed to establish treatment-only comparability."""

    protocol_version: str | None
    treatment: Treatment
    executor: ExecutorIdentity
    model: str | None
    temperature: str | None
    reasoning_configuration: str | None
    environment: ExecutionEnvironment
    task_sample: TaskSampleManifest
    attempts: int | None
    token_budget: int | None
    cost_budget: Decimal | None
    wall_time_limit: Decimal | None
    verification_identity: str | None
    acceptance_identity: str | None
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (("attempts", self.attempts), ("token_budget", self.token_budget),
                            ("cost_budget", self.cost_budget), ("wall_time_limit", self.wall_time_limit)):
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative when present")
        if self.treatment.name not in {item.value for item in P82Treatment}:
            raise ValueError("P8.2 run treatment must be one of A, B, C, or D")

    def _control_dict(self) -> dict[str, Any]:
        value = self.to_dict()
        value.pop("treatment")
        return value

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "protocol_version": self.protocol_version,
            "treatment": self.treatment.to_dict(),
            "executor": self.executor.to_dict(),
            "model": self.model,
            "temperature": self.temperature,
            "reasoning_configuration": self.reasoning_configuration,
            "environment": self.environment.to_dict(),
            "task_sample": self.task_sample.to_dict(),
            "attempts": self.attempts,
            "token_budget": self.token_budget,
            "cost_budget": self.cost_budget,
            "wall_time_limit": self.wall_time_limit,
            "verification_identity": self.verification_identity,
            "acceptance_identity": self.acceptance_identity,
        }

    def to_json(self) -> str:
        return _json(self.to_dict())

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "P82RunManifest":
        executor = ExecutorIdentity(**value["executor"])
        environment = ExecutionEnvironment(**value["environment"])
        budget_fields = {
            "max_tokens": value["token_budget"], "max_cost": value["cost_budget"],
            "max_wall_time": value["wall_time_limit"], "max_attempts": value["attempts"],
            "max_executor_invocations": None,
        }
        # P8.2 records its budget fields explicitly; qualification can still
        # receive the resulting ExecutionBudget without inventing a limit.
        budget_fields["max_cost"] = None if budget_fields["max_cost"] is None else Decimal(str(budget_fields["max_cost"]))
        budget_fields["max_wall_time"] = None if budget_fields["max_wall_time"] is None else Decimal(str(budget_fields["max_wall_time"]))
        treatment = Treatment(value["treatment"]["name"], tuple(Mechanism(item) for item in value["treatment"]["enabled_mechanisms"]))
        return cls(
            protocol_version=value.get("protocol_version"), treatment=treatment, executor=executor,
            model=value.get("model"), temperature=value.get("temperature"),
            reasoning_configuration=value.get("reasoning_configuration"), environment=environment,
            task_sample=TaskSampleManifest.from_dict(value["task_sample"]), attempts=value.get("attempts"),
            token_budget=value.get("token_budget"), cost_budget=budget_fields["max_cost"],
            wall_time_limit=budget_fields["max_wall_time"], verification_identity=value.get("verification_identity"),
            acceptance_identity=value.get("acceptance_identity"), schema_version=value.get("schema_version", SCHEMA_VERSION),
        )


@dataclass(frozen=True)
class P82Observation:
    status: P82RunStatus
    verified_acceptance: bool | None = None
    cost_to_acceptance: Decimal | None = None
    tokens_to_acceptance: int | None = None
    wall_time_seconds: Decimal | None = None
    model_calls: int | None = None
    turns: int | None = None
    repeated_exploration: int | None = None
    repeated_file_reads_searches: int | None = None
    edit_failures: int | None = None
    retries: int | None = None
    replans: int | None = None
    unnecessary_diff: int | None = None
    regressions: int | None = None
    human_intervention: int | None = None
    false_pass_evidence: bool | None = None
    verification_outcome: str | None = None

    def __post_init__(self) -> None:
        for name in ("tokens_to_acceptance", "model_calls", "turns", "repeated_exploration",
                     "repeated_file_reads_searches", "edit_failures", "retries", "replans",
                     "unnecessary_diff", "regressions", "human_intervention"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative when present")
        for name in ("cost_to_acceptance", "wall_time_seconds"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative when present")

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status.value, **{name: getattr(self, name) for name in (
            "verified_acceptance", "cost_to_acceptance", "tokens_to_acceptance", "wall_time_seconds",
            "model_calls", "turns", "repeated_exploration", "repeated_file_reads_searches",
            "edit_failures", "retries", "replans", "unnecessary_diff", "regressions",
            "human_intervention", "false_pass_evidence", "verification_outcome")}}

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "P82Observation":
        values = dict(value)
        values["status"] = P82RunStatus(values["status"])
        for name in ("cost_to_acceptance", "wall_time_seconds"):
            if values.get(name) is not None:
                values[name] = Decimal(str(values[name]))
        return cls(**values)

    def to_json(self) -> str:
        return _json(self.to_dict())


@dataclass(frozen=True)
class P82ObservationRecord:
    run: P82RunManifest
    observation: P82Observation

    def to_dict(self) -> dict[str, Any]:
        return {"run": self.run.to_dict(), "observation": self.observation.to_dict()}

    def to_json(self) -> str:
        return _json(self.to_dict())


@dataclass(frozen=True)
class P82TreatmentSummary:
    treatment: str
    record_count: int
    executed_count: int
    not_executed_count: int
    blocked_count: int
    verified_acceptance_rate: Decimal | None
    median_cost_to_acceptance: Decimal | None
    median_tokens_to_acceptance: Decimal | None
    false_pass_rate: Decimal | None

    def to_dict(self) -> dict[str, Any]:
        return {name: getattr(self, name) for name in (
            "treatment", "record_count", "executed_count", "not_executed_count", "blocked_count",
            "verified_acceptance_rate", "median_cost_to_acceptance", "median_tokens_to_acceptance",
            "false_pass_rate")}


def p82_manifest() -> tuple[Treatment, ...]:
    """Return the canonical A/B/C/D arms in experimental order."""

    return tuple(_treatment(name) for name in P82Treatment)


def build_p82_plan(config: P82ExperimentConfig) -> P82ExperimentPlan:
    """Create deterministic plans without executing or fabricating results."""

    treatments = p82_manifest()
    trials = tuple(
        P82TrialPlan(treatment, task, replicate)
        for task in config.tasks
        for replicate in config.replicate_ids
        for treatment in treatments
    )
    return P82ExperimentPlan(config, treatments, trials)


def plan_is_comparable(plan: P82ExperimentPlan) -> bool | None:
    """Return True when all shared controls are known, otherwise None.

    There is no False result: a generated plan has one frozen control set, so
    missing evidence remains unknown rather than being treated as a mismatch.
    """

    values = (
        plan.config.executor.version,
        plan.config.executor.configuration_digest,
        plan.config.model,
        plan.config.environment.repository_revision,
        plan.config.environment.runtime,
        plan.config.environment.platform,
        plan.config.environment.toolchain,
        plan.config.environment.environment_digest,
        plan.config.budget.max_tokens,
        plan.config.budget.max_cost,
        plan.config.budget.max_wall_time,
        plan.config.budget.max_attempts,
        plan.config.budget.max_executor_invocations,
        plan.config.verification_contract,
        plan.config.acceptance_authority,
    )
    return None if any(value is None for value in values) else True


def compare_run_manifests(left: P82RunManifest, right: P82RunManifest) -> P82Comparability:
    """Compare runs while excluding treatment and preserving insufficient data."""

    left_values, right_values = left._control_dict(), right._control_dict()
    if any(value is None for value in _flatten_values(left_values)) or any(value is None for value in _flatten_values(right_values)):
        return P82Comparability.INDETERMINATE
    return P82Comparability.COMPARABLE if left_values == right_values else P82Comparability.NOT_COMPARABLE


def _flatten_values(value: Any) -> Iterable[Any]:
    if isinstance(value, dict):
        for item in value.values():
            yield from _flatten_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _flatten_values(item)
    else:
        yield value


def summarize_p82(records: tuple[P82ObservationRecord, ...]) -> tuple[P82TreatmentSummary, ...]:
    """Aggregate observations by arm without treating unavailable data as zero."""

    result = []
    for treatment in P82Treatment:
        selected = tuple(record for record in records if record.run.treatment.name == treatment.value)
        executed = tuple(record for record in selected if record.observation.status is P82RunStatus.EXECUTED)
        accepted = tuple(record.observation.verified_acceptance for record in executed if record.observation.verified_acceptance is not None)
        accepted_costs = tuple(record.observation.cost_to_acceptance for record in executed if record.observation.verified_acceptance is True and record.observation.cost_to_acceptance is not None)
        accepted_tokens = tuple(record.observation.tokens_to_acceptance for record in executed if record.observation.verified_acceptance is True and record.observation.tokens_to_acceptance is not None)
        false_pass = tuple(record.observation.false_pass_evidence for record in selected if record.observation.false_pass_evidence is not None)
        result.append(P82TreatmentSummary(
            treatment=treatment.value,
            record_count=len(selected),
            executed_count=len(executed),
            not_executed_count=sum(record.observation.status is P82RunStatus.NOT_EXECUTED for record in selected),
            blocked_count=sum(record.observation.status is P82RunStatus.BLOCKED for record in selected),
            verified_acceptance_rate=None if not accepted else Decimal(sum(accepted)) / Decimal(len(accepted)),
            median_cost_to_acceptance=None if not accepted_costs else median(accepted_costs),
            median_tokens_to_acceptance=None if not accepted_tokens else Decimal(str(median(accepted_tokens))),
            false_pass_rate=None if not false_pass else Decimal(sum(false_pass)) / Decimal(len(false_pass)),
        ))
    return tuple(result)
