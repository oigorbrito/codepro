"""Pure experimental composition contracts for P7.

P7 describes treatment arms and records externally supplied observations. It
does not execute mechanisms, select executors, or make acceptance decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Any, Mapping


SCHEMA_VERSION = 1


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class Mechanism(_ValueEnum):
    P1_CHARACTERIZATION = "P1_CHARACTERIZATION"
    P2_PROGRESS = "P2_PROGRESS"
    P3_ROUTING = "P3_ROUTING"
    P4_PLANNING_STATE = "P4_PLANNING_STATE"
    P5_PATCH_VERIFICATION = "P5_PATCH_VERIFICATION"
    P6_HANDOFF_ACCOUNTING = "P6_HANDOFF_ACCOUNTING"
    P8_SAFE_EDITOR = "P8_SAFE_EDITOR"
    P8_ENHANCED_REPOSITORY_CONTEXT = "P8_ENHANCED_REPOSITORY_CONTEXT"


_MECHANISM_ORDER = {mechanism: index for index, mechanism in enumerate(Mechanism)}


class ComparabilityStatus(_ValueEnum):
    COMPARABLE = "COMPARABLE"
    INCOMPARABLE = "INCOMPARABLE"
    UNKNOWN = "UNKNOWN"


def _json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _measurement_items(items: tuple[tuple[str, Any], ...]) -> tuple[tuple[str, Any], ...]:
    if any(not key for key, _ in items):
        raise ValueError("Measurement keys must be non-empty")
    keys = [key for key, _ in items]
    if len(set(keys)) != len(keys):
        raise ValueError("Measurement keys must be unique")
    return tuple(sorted(items, key=lambda item: item[0]))


@dataclass(frozen=True)
class Treatment:
    name: str
    enabled_mechanisms: tuple[Mechanism, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Treatment names must be non-empty")
        mechanisms = tuple(self.enabled_mechanisms)
        if len(set(mechanisms)) != len(mechanisms):
            raise ValueError("A treatment cannot enable a mechanism twice")
        object.__setattr__(self, "enabled_mechanisms", tuple(sorted(mechanisms, key=_MECHANISM_ORDER.__getitem__)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "enabled_mechanisms": [mechanism.value for mechanism in self.enabled_mechanisms],
        }


@dataclass(frozen=True)
class ExperimentIdentity:
    task: str | None
    executor: str | None
    model: str | None
    environment: str | None
    budget: str | None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "task": self.task,
            "executor": self.executor,
            "model": self.model,
            "environment": self.environment,
            "budget": self.budget,
        }


@dataclass(frozen=True)
class TrialObservation:
    identity: ExperimentIdentity
    treatment: Treatment
    measurements: tuple[tuple[str, Any], ...] = ()
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "measurements", _measurement_items(tuple(self.measurements)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "identity": self.identity.to_dict(),
            "treatment": self.treatment.to_dict(),
            "measurements": {key: value for key, value in self.measurements},
        }

    def to_json(self) -> str:
        return _json(self.to_dict())


@dataclass(frozen=True)
class ExperimentManifest:
    treatments: tuple[Treatment, ...]
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        treatments = tuple(sorted(self.treatments, key=lambda treatment: treatment.name))
        names = [treatment.name for treatment in treatments]
        if len(set(names)) != len(names):
            raise ValueError("Treatment names must be unique within a manifest")
        compositions = [treatment.enabled_mechanisms for treatment in treatments]
        if len(set(compositions)) != len(compositions):
            raise ValueError("Semantically identical treatments are not allowed in one manifest")
        object.__setattr__(self, "treatments", treatments)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "treatments": [treatment.to_dict() for treatment in self.treatments],
        }

    def to_json(self) -> str:
        return _json(self.to_dict())


@dataclass(frozen=True)
class ExperimentSummary:
    trial_count: int
    treatment_names: tuple[str, ...]
    comparability: ComparabilityStatus
    measurement_keys: tuple[str, ...]
    measurement_counts: tuple[tuple[str, int], ...]
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "trial_count": self.trial_count,
            "treatment_names": list(self.treatment_names),
            "comparability": self.comparability.value,
            "measurement_keys": list(self.measurement_keys),
            "measurement_counts": {key: count for key, count in self.measurement_counts},
        }

    def to_json(self) -> str:
        return _json(self.to_dict())


def initial_manifest() -> ExperimentManifest:
    """Return only the P7 A-F treatment arms; P8.2 is a separate manifest."""

    return ExperimentManifest(
        treatments=(
            Treatment("A", ()),
            Treatment("B", (Mechanism.P1_CHARACTERIZATION,)),
            Treatment("C", (Mechanism.P1_CHARACTERIZATION, Mechanism.P2_PROGRESS)),
            Treatment("D", (Mechanism.P1_CHARACTERIZATION, Mechanism.P2_PROGRESS, Mechanism.P3_ROUTING)),
            Treatment("E", (Mechanism.P4_PLANNING_STATE,)),
            Treatment("F", (Mechanism.P5_PATCH_VERIFICATION,)),
        )
    )


def compare_trials(left: TrialObservation, right: TrialObservation) -> ComparabilityStatus:
    """Compare only controlled identity dimensions; treatment remains declarative."""

    left_values = left.identity.to_dict()
    right_values = right.identity.to_dict()
    if any(left_values[key] is None or right_values[key] is None for key in left_values):
        return ComparabilityStatus.UNKNOWN
    if left_values != right_values:
        return ComparabilityStatus.INCOMPARABLE
    return ComparabilityStatus.COMPARABLE


def summarize_trials(trials: tuple[TrialObservation, ...]) -> ExperimentSummary:
    """Aggregate observations without imputing absent measurements or accepting work."""

    trials = tuple(trials)
    if not trials:
        comparability = ComparabilityStatus.UNKNOWN
    else:
        statuses = tuple(compare_trials(trials[0], trial) for trial in trials[1:])
        comparability = (
            ComparabilityStatus.INCOMPARABLE
            if ComparabilityStatus.INCOMPARABLE in statuses
            else ComparabilityStatus.UNKNOWN
            if ComparabilityStatus.UNKNOWN in statuses
            else ComparabilityStatus.COMPARABLE
        )
    counts: dict[str, int] = {}
    for trial in trials:
        for key, _ in trial.measurements:
            counts[key] = counts.get(key, 0) + 1
    return ExperimentSummary(
        trial_count=len(trials),
        treatment_names=tuple(sorted({trial.treatment.name for trial in trials})),
        comparability=comparability,
        measurement_keys=tuple(sorted(counts)),
        measurement_counts=tuple(sorted(counts.items())),
    )
