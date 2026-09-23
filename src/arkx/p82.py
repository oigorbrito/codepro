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
from typing import Any

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
