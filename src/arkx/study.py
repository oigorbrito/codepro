"""Versioned pre-execution study specification for empirical CodePro experiments."""

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
        raise ValueError(f"Unsupported study spec schema: {raw}")
    return raw


def _required_string(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _optional_string(name: str, value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string when present")
    return value


def _string_tuple(name: str, value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{name} must be a list or tuple")
    if any(not isinstance(item, str) for item in value):
        raise ValueError(f"{name} must contain only strings")
    return tuple(value)


def _strict_int(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    return value


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class Methodology(_ValueEnum):
    BENCHMARKING = "BENCHMARKING"
    ENGINEERING_RESEARCH_BENCHMARKING = "ENGINEERING_RESEARCH_BENCHMARKING"


class ComparisonMode(_ValueEnum):
    CONTROL_TREATMENT = "CONTROL_TREATMENT"
    BENCHMARK_ONLY = "BENCHMARK_ONLY"
    NO_COMPARATOR_JUSTIFIED = "NO_COMPARATOR_JUSTIFIED"


class RawResultsPolicy(_ValueEnum):
    PERSIST_ALL_RAW_RUNS = "PERSIST_ALL_RAW_RUNS"


def _values(items: tuple[str, ...]) -> list[str]:
    return sorted(set(items))


def _required_text(name: str, value: str, issues: list[str]) -> None:
    if not value.strip():
        issues.append(f"{name} must be non-empty")


@dataclass(frozen=True)
class StudySpec:
    study_id: str
    methodology: Methodology
    research_question: str
    hypothesis: str
    experimental_unit: str
    quality_attribute: str
    workload_refs: tuple[str, ...]
    metrics: tuple[str, ...]
    primary_metric: str
    comparison_mode: ComparisonMode
    treatment_refs: tuple[str, ...]
    stopping_rule: str
    analysis_plan_ref: str
    promotion_rule: str
    environment_contract_ref: str
    repetitions: int = 1
    repetition_justification: str | None = None
    control_ref: str | None = None
    comparator_justification: str | None = None
    raw_results_policy: RawResultsPolicy = RawResultsPolicy.PERSIST_ALL_RAW_RUNS
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "study_id": self.study_id,
            "methodology": self.methodology.value,
            "research_question": self.research_question,
            "hypothesis": self.hypothesis,
            "experimental_unit": self.experimental_unit,
            "quality_attribute": self.quality_attribute,
            "workload_refs": _values(self.workload_refs),
            "metrics": _values(self.metrics),
            "primary_metric": self.primary_metric,
            "comparison_mode": self.comparison_mode.value,
            "control_ref": self.control_ref,
            "treatment_refs": _values(self.treatment_refs),
            "comparator_justification": self.comparator_justification,
            "repetitions": self.repetitions,
            "repetition_justification": self.repetition_justification,
            "stopping_rule": self.stopping_rule,
            "analysis_plan_ref": self.analysis_plan_ref,
            "promotion_rule": self.promotion_rule,
            "environment_contract_ref": self.environment_contract_ref,
            "raw_results_policy": self.raw_results_policy.value,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "StudySpec":
        if not isinstance(value, Mapping):
            raise ValueError("study spec payload must be a mapping")
        schema_version = _strict_schema(value)
        return cls(
            study_id=_required_string("study_id", value.get("study_id")),
            methodology=Methodology(value["methodology"]),
            research_question=_required_string("research_question", value.get("research_question")),
            hypothesis=_required_string("hypothesis", value.get("hypothesis")),
            experimental_unit=_required_string("experimental_unit", value.get("experimental_unit")),
            quality_attribute=_required_string("quality_attribute", value.get("quality_attribute")),
            workload_refs=_string_tuple("workload_refs", value.get("workload_refs", ())),
            metrics=_string_tuple("metrics", value.get("metrics", ())),
            primary_metric=_required_string("primary_metric", value.get("primary_metric")),
            comparison_mode=ComparisonMode(value["comparison_mode"]),
            control_ref=_optional_string("control_ref", value.get("control_ref")),
            treatment_refs=_string_tuple("treatment_refs", value.get("treatment_refs", ())),
            comparator_justification=_optional_string("comparator_justification", value.get("comparator_justification")),
            repetitions=_strict_int("repetitions", value.get("repetitions", 1)),
            repetition_justification=_optional_string("repetition_justification", value.get("repetition_justification")),
            stopping_rule=_required_string("stopping_rule", value.get("stopping_rule")),
            analysis_plan_ref=_required_string("analysis_plan_ref", value.get("analysis_plan_ref")),
            promotion_rule=_required_string("promotion_rule", value.get("promotion_rule")),
            environment_contract_ref=_required_string("environment_contract_ref", value.get("environment_contract_ref")),
            raw_results_policy=RawResultsPolicy(value.get("raw_results_policy", RawResultsPolicy.PERSIST_ALL_RAW_RUNS.value)),
            schema_version=schema_version,
        )

    @classmethod
    def from_json(cls, value: str) -> "StudySpec":
        return cls.from_dict(json.loads(value))


@dataclass(frozen=True)
class FrozenStudySpec:
    study_spec: StudySpec
    content_hash: str
    freeze_schema_version: int = FREEZE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "freeze_schema_version": self.freeze_schema_version,
            "content_hash": self.content_hash,
            "study_spec": self.study_spec.to_dict(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def validate_study_spec(spec: StudySpec) -> tuple[str, ...]:
    issues: list[str] = []
    for name in (
        "study_id",
        "research_question",
        "hypothesis",
        "experimental_unit",
        "quality_attribute",
        "primary_metric",
        "stopping_rule",
        "analysis_plan_ref",
        "promotion_rule",
        "environment_contract_ref",
    ):
        _required_text(name, str(getattr(spec, name)), issues)

    if not spec.workload_refs:
        issues.append("workload_refs must contain at least one immutable or versioned reference")
    if not spec.metrics:
        issues.append("metrics must contain at least one metric")
    if spec.primary_metric not in spec.metrics:
        issues.append("primary_metric must be included in metrics")
    if spec.repetitions < 1:
        issues.append("repetitions must be at least 1")
    if spec.repetitions == 1 and not (spec.repetition_justification or "").strip():
        issues.append("single-run studies require repetition_justification")

    if spec.comparison_mode is ComparisonMode.CONTROL_TREATMENT:
        if not (spec.control_ref or "").strip():
            issues.append("CONTROL_TREATMENT requires control_ref")
        if not spec.treatment_refs:
            issues.append("CONTROL_TREATMENT requires at least one treatment_ref")
        if spec.control_ref and spec.control_ref in spec.treatment_refs:
            issues.append("control_ref must be distinct from treatment_refs")
    elif spec.comparison_mode is ComparisonMode.BENCHMARK_ONLY:
        if not spec.treatment_refs:
            issues.append("BENCHMARK_ONLY requires at least one system/configuration reference")
    elif spec.comparison_mode is ComparisonMode.NO_COMPARATOR_JUSTIFIED:
        if not (spec.comparator_justification or "").strip():
            issues.append("NO_COMPARATOR_JUSTIFIED requires comparator_justification")

    if spec.raw_results_policy is not RawResultsPolicy.PERSIST_ALL_RAW_RUNS:
        issues.append("raw results policy must preserve every raw run")

    return tuple(sorted(set(issues)))


def freeze_study_spec(spec: StudySpec) -> FrozenStudySpec:
    """Validate and content-address a study design before any treatment run.

    The content hash proves integrity, not temporal precedence. A run must also
    reference an immutable commit/blob that existed before execution.
    """

    issues = validate_study_spec(spec)
    if issues:
        raise ValueError("Invalid study spec: " + "; ".join(issues))
    content_hash = hashlib.sha256(spec.to_json().encode("utf-8")).hexdigest()
    return FrozenStudySpec(study_spec=spec, content_hash=f"sha256:{content_hash}")
