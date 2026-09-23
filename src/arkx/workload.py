"""Frozen workload manifest for reproducible Arkx benchmark studies."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping


SCHEMA_VERSION = 1
FREEZE_SCHEMA_VERSION = 1


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
        schema_version = int(value.get("schema_version", 0))
        if schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported workload manifest schema: {schema_version}")
        return cls(
            workload_id=str(value["workload_id"]),
            source_ref=str(value["source_ref"]),
            source_version=str(value["source_version"]),
            target_population=str(value["target_population"]),
            sampling_strategy=SamplingStrategy(value["sampling_strategy"]),
            selection_rule=str(value["selection_rule"]),
            selection_justification=str(value["selection_justification"]),
            inclusion_criteria=tuple(value.get("inclusion_criteria", ())),
            exclusion_criteria=tuple(value.get("exclusion_criteria", ())),
            task_refs=tuple(value.get("task_refs", ())),
            holdout_policy=str(value["holdout_policy"]),
            task_order_policy=TaskOrderPolicy(value["task_order_policy"]),
            random_seed=value.get("random_seed"),
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
