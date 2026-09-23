"""Deterministic repository state and plan artifacts for P4."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Any


SCHEMA_VERSION = 1


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class StepStatus(_ValueEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"


class ReplanTrigger(_ValueEnum):
    DEPENDENCY_DISCOVERED = "DEPENDENCY_DISCOVERED"
    EXPECTED_FILE_MISSING = "EXPECTED_FILE_MISSING"
    TEST_SURFACE_CHANGED = "TEST_SURFACE_CHANGED"
    ASSUMPTION_INVALIDATED = "ASSUMPTION_INVALIDATED"
    BLOCKED_STEP = "BLOCKED_STEP"
    SCOPE_EXPANDED = "SCOPE_EXPANDED"


def _values(items: tuple[str, ...] | None) -> list[str] | None:
    return None if items is None else sorted(set(items))


@dataclass(frozen=True)
class RepositoryState:
    relevant_files: tuple[str, ...] | None = None
    dependency_edges: tuple[tuple[str, str], ...] | None = None
    impacted_components: tuple[str, ...] | None = None
    affected_tests: tuple[str, ...] | None = None
    assumptions: tuple[str, ...] | None = None
    unresolved_questions: tuple[str, ...] | None = None
    completed_steps: tuple[str, ...] | None = None
    remaining_steps: tuple[str, ...] | None = None
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        edges = None if self.dependency_edges is None else [list(edge) for edge in sorted(set(self.dependency_edges))]
        return {
            "schema_version": self.schema_version,
            "relevant_files": _values(self.relevant_files),
            "dependency_edges": edges,
            "impacted_components": _values(self.impacted_components),
            "affected_tests": _values(self.affected_tests),
            "assumptions": _values(self.assumptions),
            "unresolved_questions": _values(self.unresolved_questions),
            "completed_steps": _values(self.completed_steps),
            "remaining_steps": _values(self.remaining_steps),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class PlanStep:
    step_id: str
    goal: str
    status: StepStatus = StepStatus.PENDING
    depends_on: tuple[str, ...] = ()
    expected_files: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "goal": self.goal,
            "status": self.status.value,
            "depends_on": sorted(set(self.depends_on)),
            "expected_files": sorted(set(self.expected_files)),
        }


@dataclass(frozen=True)
class RepositoryPlan:
    goal: str
    steps: tuple[PlanStep, ...]
    dependencies: tuple[tuple[str, str], ...]
    acceptance_criteria: tuple[str, ...]
    expected_files: tuple[str, ...]
    replan_triggers: tuple[ReplanTrigger, ...]
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "goal": self.goal,
            "steps": [step.to_dict() for step in sorted(self.steps, key=lambda item: item.step_id)],
            "dependencies": [list(edge) for edge in sorted(set(self.dependencies))],
            "acceptance_criteria": _values(self.acceptance_criteria),
            "expected_files": _values(self.expected_files),
            "replan_triggers": sorted(trigger.value for trigger in set(self.replan_triggers)),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def build_plan(
    goal: str,
    steps: tuple[PlanStep, ...],
    *,
    dependencies: tuple[tuple[str, str], ...] = (),
    acceptance_criteria: tuple[str, ...] = (),
    expected_files: tuple[str, ...] = (),
    replan_triggers: tuple[ReplanTrigger, ...] = (),
) -> RepositoryPlan:
    """Build and validate a plan without marking steps complete."""

    ids = {step.step_id for step in steps}
    if len(ids) != len(steps) or "" in ids:
        raise ValueError("Plan step identities must be unique and non-empty")
    edges = set(dependencies)
    for step in steps:
        unknown = set(step.depends_on) - ids
        if unknown:
            raise ValueError(f"Unknown step dependencies: {sorted(unknown)}")
        edges.update((dependency, step.step_id) for dependency in step.depends_on)
    _assert_acyclic(ids, edges)
    return RepositoryPlan(
        goal=goal,
        steps=tuple(steps),
        dependencies=tuple(edges),
        acceptance_criteria=acceptance_criteria,
        expected_files=expected_files,
        replan_triggers=replan_triggers,
    )


def _assert_acyclic(nodes: set[str], edges: set[tuple[str, str]]) -> None:
    graph = {node: [] for node in nodes}
    for source, target in edges:
        if source not in nodes or target not in nodes:
            raise ValueError("Plan dependency references an unknown step")
        graph[source].append(target)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise ValueError("Plan dependencies contain a cycle")
        if node in visited:
            return
        visiting.add(node)
        for child in graph[node]:
            visit(child)
        visiting.remove(node)
        visited.add(node)

    for node in sorted(nodes):
        visit(node)


def plan_repository(goal: str, state: RepositoryState) -> RepositoryPlan:
    """Create a small deterministic plan from explicit repository state."""

    files = tuple(state.relevant_files or ())
    components = tuple(state.impacted_components or ())
    steps = tuple(
        PlanStep(
            step_id=f"inspect-{index:02d}",
            goal=f"Inspect component {component}",
            expected_files=tuple(file for file in files if component in file),
        )
        for index, component in enumerate(sorted(set(components)), start=1)
    )
    test_step = PlanStep(
        step_id="verify-affected-tests",
        goal="Verify affected tests",
        depends_on=tuple(step.step_id for step in steps),
        expected_files=tuple(state.affected_tests or ()),
    )
    all_steps = steps + (test_step,)
    return build_plan(
        goal,
        all_steps,
        acceptance_criteria=("all planned steps have explicit outcomes",),
        expected_files=files,
        replan_triggers=(ReplanTrigger.DEPENDENCY_DISCOVERED, ReplanTrigger.BLOCKED_STEP),
    )


@dataclass(frozen=True)
class ReplanRequest:
    trigger: ReplanTrigger
    previous_plan_ref: str
    evidence_refs: tuple[str, ...]
    remaining_budget: int | None
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "trigger": self.trigger.value,
            "previous_plan_ref": self.previous_plan_ref,
            "evidence_refs": _values(self.evidence_refs),
            "remaining_budget": self.remaining_budget,
        }


@dataclass(frozen=True)
class ReplanResult:
    previous_plan_ref: str
    new_plan: RepositoryPlan
    trigger: ReplanTrigger
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "previous_plan_ref": self.previous_plan_ref,
            "trigger": self.trigger.value,
            "new_plan": self.new_plan.to_dict(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

