"""Frozen workload manifest for reproducible Arkx benchmark studies."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping


SCHEMA_VERSION = 1
FREEZE_SCHEMA_VERSION = 1


def _strict_schema(value: Mapping[str, Any]) -> int:
    raw = value.get("schema_version", 0)
    if isinstance(raw, bool) or not isinstance(raw, int) or raw != SCHEMA_VERSION:
        raise ValueError(f"Unsupported workload manifest schema: {raw}")
    return raw


def _required_string(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _string_tuple(name: str, value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{name} must be a list or tuple")
    if any(not isinstance(item, str) for item in value):
        raise ValueError(f"{name} must contain only strings")
    return tuple(value)


def _optional_int(name: str, value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer when present")
    return value


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class SamplingStrategy(_ValueEnum):
    FULL_POPULATION = "FULL_POPULATION"
    FIXED_SAMPLE = "FIXED_SAMPLE"
    STRATIFIED_FIXED_SAMPLE = "STRATIFIED_FIXED_SAMPLE"
    RANDOM_SAMPLE = "RANDOM_SAMPLE"


class TaskOrderPolicy(_ValueEnum):
    FIXED = "FIXED"
    RANDOMIZED = "RANDOMIZED"


@dataclass(frozen=True)
class WorkloadManifest:
    workload_id: str
    source_ref: str
    source_version: str
    target_population: str
    sampling_strategy: SamplingStrategy
    selection_rule: str
    selection_justification: str
    inclusion_criteria: tuple[str, ...]
    exclusion_criteria: tuple[str, ...]
    task_refs: tuple[str, ...]
    holdout_policy: str
    task_order_policy: TaskOrderPolicy
    random_seed: int | None = None
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "workload_id": self.workload_id,
            "source_ref": self.source_ref,
            "source_version": self.source_version,
            "target_population": self.target_population,
            "sampling_strategy": self.sampling_strategy.value,
            "selection_rule": self.selection_rule,
            "selection_justification": self.selection_justification,
            "inclusion_criteria": sorted(set(self.inclusion_criteria)),
            "exclusion_criteria": sorted(set(self.exclusion_criteria)),
            "task_refs": list(self.task_refs),
            "holdout_policy": self.holdout_policy,
            "task_order_policy": self.task_order_policy.value,
            "random_seed": self.random_seed,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "WorkloadManifest":
        if not isinstance(value, Mapping):
            raise ValueError("workload manifest payload must be a mapping")
        schema_version = _strict_schema(value)
        return cls(
            workload_id=_required_string("workload_id", value.get("workload_id")),
            source_ref=_required_string("source_ref", value.get("source_ref")),
            source_version=_required_string("source_version", value.get("source_version")),
            target_population=_required_string("target_population", value.get("target_population")),
            sampling_strategy=SamplingStrategy(value["sampling_strategy"]),
            selection_rule=_required_string("selection_rule", value.get("selection_rule")),
            selection_justification=_required_string("selection_justification", value.get("selection_justification")),
            inclusion_criteria=_string_tuple("inclusion_criteria", value.get("inclusion_criteria", ())),
            exclusion_criteria=_string_tuple("exclusion_criteria", value.get("exclusion_criteria", ())),
            task_refs=_string_tuple("task_refs", value.get("task_refs", ())),
            holdout_policy=_required_string("holdout_policy", value.get("holdout_policy")),
            task_order_policy=TaskOrderPolicy(value["task_order_policy"]),
            random_seed=_optional_int("random_seed", value.get("random_seed")),
            schema_version=schema_version,
        )

    @classmethod
    def from_json(cls, value: str) -> "WorkloadManifest":
        return cls.from_dict(json.loads(value))


@dataclass(frozen=True)
class FrozenWorkloadManifest:
    workload: WorkloadManifest
    content_hash: str
    freeze_schema_version: int = FREEZE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "freeze_schema_version": self.freeze_schema_version,
            "content_hash": self.content_hash,
            "workload": self.workload.to_dict(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _required(name: str, value: str, issues: list[str]) -> None:
    if not value.strip():
        issues.append(f"{name} must be non-empty")


def validate_workload_manifest(workload: WorkloadManifest) -> tuple[str, ...]:
    issues: list[str] = []
    for name in (
        "workload_id",
        "source_ref",
        "source_version",
        "target_population",
        "selection_rule",
        "selection_justification",
        "holdout_policy",
    ):
        _required(name, str(getattr(workload, name)), issues)

    if not workload.task_refs:
        issues.append("task_refs must contain at least one frozen task")
    if len(set(workload.task_refs)) != len(workload.task_refs):
        issues.append("task_refs must not contain duplicates")
    if any(not task.strip() for task in workload.task_refs):
        issues.append("task_refs cannot contain blank entries")
    if workload.task_order_policy is TaskOrderPolicy.RANDOMIZED and workload.random_seed is None:
        issues.append("RANDOMIZED task order requires random_seed")
    if workload.sampling_strategy is SamplingStrategy.RANDOM_SAMPLE and workload.random_seed is None:
        issues.append("RANDOM_SAMPLE requires random_seed")
    if set(workload.inclusion_criteria) & set(workload.exclusion_criteria):
        issues.append("the same criterion cannot be both inclusion and exclusion")

    return tuple(sorted(set(issues)))


def freeze_workload_manifest(workload: WorkloadManifest) -> FrozenWorkloadManifest:
    issues = validate_workload_manifest(workload)
    if issues:
        raise ValueError("Invalid workload manifest: " + "; ".join(issues))
    digest = hashlib.sha256(workload.to_json().encode("utf-8")).hexdigest()
    return FrozenWorkloadManifest(workload=workload, content_hash=f"sha256:{digest}")
