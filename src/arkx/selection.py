"""Explicit treatment, capability and executor selection contracts.

Selection happens after routing and never falls back silently. Qualification
evidence is required before an executor can be selected for a treatment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Any

from .characterization import RecommendedPath
from .composition import Mechanism, Treatment
from .executor_qualification import ExecutorIdentity, QualificationStatus


SCHEMA_VERSION = 1


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class SelectionStatus(_ValueEnum):
    SELECTED = "SELECTED"
    BLOCKED = "BLOCKED"
    REQUIRE_QUALIFICATION = "REQUIRE_QUALIFICATION"
    UNKNOWN = "UNKNOWN"


class SelectionReason(_ValueEnum):
    SELECTED = "SELECTED"
    NO_TREATMENT_FOR_PATH = "NO_TREATMENT_FOR_PATH"
    AMBIGUOUS_TREATMENT = "AMBIGUOUS_TREATMENT"
    TREATMENT_NOT_FOUND = "TREATMENT_NOT_FOUND"
    NO_EXECUTOR_FOR_CAPABILITY = "NO_EXECUTOR_FOR_CAPABILITY"
    EXECUTOR_NOT_QUALIFIED = "EXECUTOR_NOT_QUALIFIED"
    QUALIFICATION_EVIDENCE_MISSING = "QUALIFICATION_EVIDENCE_MISSING"
    AMBIGUOUS_EXECUTOR = "AMBIGUOUS_EXECUTOR"
    CAPABILITY_MISMATCH = "CAPABILITY_MISMATCH"


def _sorted_unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(set(values)))


@dataclass(frozen=True)
class TreatmentDefinition:
    name: str
    path: RecommendedPath
    required_capabilities: tuple[str, ...] = ()
    mechanisms: tuple[Mechanism, ...] = ()
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Treatment name must be non-empty")
        if any(not value for value in self.required_capabilities):
            raise ValueError("Required capability names must be non-empty")
        object.__setattr__(self, "required_capabilities", _sorted_unique(self.required_capabilities))
        object.__setattr__(self, "mechanisms", tuple(sorted(set(self.mechanisms), key=lambda item: item.value)))

    def to_treatment(self) -> Treatment:
        return Treatment(self.name, self.mechanisms)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "path": self.path.value,
            "required_capabilities": list(self.required_capabilities),
            "mechanisms": [mechanism.value for mechanism in self.mechanisms],
        }


@dataclass(frozen=True)
class TreatmentCatalog:
    treatments: tuple[TreatmentDefinition, ...]
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        values = tuple(sorted(self.treatments, key=lambda item: item.name))
        if len({item.name for item in values}) != len(values):
            raise ValueError("Treatment names must be unique")
        object.__setattr__(self, "treatments", values)

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "treatments": [item.to_dict() for item in self.treatments]}


@dataclass(frozen=True)
class ExecutorBinding:
    executor: ExecutorIdentity
    capabilities: tuple[str, ...]
    qualification_status: QualificationStatus
    evidence_refs: tuple[str, ...] | None
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if any(not value for value in self.capabilities):
            raise ValueError("Executor capability names must be non-empty")
        object.__setattr__(self, "capabilities", _sorted_unique(self.capabilities))
        if self.evidence_refs is not None:
            object.__setattr__(self, "evidence_refs", _sorted_unique(self.evidence_refs))

    def supports(self, required: tuple[str, ...]) -> bool:
        return set(required).issubset(self.capabilities)

    def empirically_qualified(self) -> bool:
        return self.qualification_status is QualificationStatus.QUALIFIABLE and bool(self.evidence_refs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "executor": self.executor.to_dict(),
            "capabilities": list(self.capabilities),
            "qualification_status": self.qualification_status.value,
            "evidence_refs": None if self.evidence_refs is None else list(self.evidence_refs),
        }


@dataclass(frozen=True)
class ExecutorRegistry:
    bindings: tuple[ExecutorBinding, ...]
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        values = tuple(sorted(self.bindings, key=lambda item: (item.executor.name, item.executor.version or "")))
        identities = [(item.executor.name, item.executor.version, item.executor.configuration_digest) for item in values]
        if len(set(identities)) != len(identities):
            raise ValueError("Executor bindings must have unique identities")
        object.__setattr__(self, "bindings", values)

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": self.schema_version, "bindings": [item.to_dict() for item in self.bindings]}


@dataclass(frozen=True)
class SelectionDecision:
    status: SelectionStatus
    reason_codes: tuple[SelectionReason, ...]
    path: RecommendedPath | None = None
    treatment: TreatmentDefinition | None = None
    executor: ExecutorBinding | None = None
    telemetry: dict[str, Any] = field(default_factory=dict)
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status.value,
            "reason_codes": [reason.value for reason in self.reason_codes],
            "path": None if self.path is None else self.path.value,
            "treatment": None if self.treatment is None else self.treatment.to_dict(),
            "executor": None if self.executor is None else self.executor.to_dict(),
            "telemetry": self.telemetry,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def select_treatment(
    path: RecommendedPath,
    catalog: TreatmentCatalog,
    *,
    treatment_name: str | None = None,
) -> SelectionDecision:
    candidates = tuple(item for item in catalog.treatments if item.path is path)
    if treatment_name is not None:
        candidates = tuple(item for item in candidates if item.name == treatment_name)
        if not candidates:
            return SelectionDecision(SelectionStatus.BLOCKED, (SelectionReason.TREATMENT_NOT_FOUND,), path=path)
    if not candidates:
        return SelectionDecision(SelectionStatus.BLOCKED, (SelectionReason.NO_TREATMENT_FOR_PATH,), path=path)
    if len(candidates) > 1:
        return SelectionDecision(SelectionStatus.REQUIRE_QUALIFICATION, (SelectionReason.AMBIGUOUS_TREATMENT,), path=path)
    selected = candidates[0]
    return SelectionDecision(SelectionStatus.SELECTED, (SelectionReason.SELECTED,), path=path, treatment=selected)


def select_executor(treatment: TreatmentDefinition, registry: ExecutorRegistry) -> SelectionDecision:
    candidates = tuple(binding for binding in registry.bindings if binding.supports(treatment.required_capabilities))
    if not candidates:
        return SelectionDecision(SelectionStatus.BLOCKED, (SelectionReason.NO_EXECUTOR_FOR_CAPABILITY,), path=treatment.path, treatment=treatment)
    qualified = tuple(binding for binding in candidates if binding.empirically_qualified())
    if not qualified:
        reason = SelectionReason.QUALIFICATION_EVIDENCE_MISSING if any(binding.evidence_refs in (None, ()) for binding in candidates) else SelectionReason.EXECUTOR_NOT_QUALIFIED
        return SelectionDecision(SelectionStatus.REQUIRE_QUALIFICATION, (reason,), path=treatment.path, treatment=treatment)
    if len(qualified) > 1:
        return SelectionDecision(SelectionStatus.REQUIRE_QUALIFICATION, (SelectionReason.AMBIGUOUS_EXECUTOR,), path=treatment.path, treatment=treatment)
    selected = qualified[0]
    return SelectionDecision(SelectionStatus.SELECTED, (SelectionReason.SELECTED,), path=treatment.path, treatment=treatment, executor=selected)
