"""Pre-execution statistical analysis plan for Arkx empirical studies."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping

from arkx.study import FrozenStudySpec, StudySpec, freeze_study_spec


SCHEMA_VERSION = 1
FREEZE_SCHEMA_VERSION = 1


def _strict_schema(value: Mapping[str, Any]) -> int:
    raw = value.get("schema_version", 0)
    if isinstance(raw, bool) or not isinstance(raw, int) or raw != SCHEMA_VERSION:
        raise ValueError(f"Unsupported analysis plan schema: {raw}")
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


def _optional_float(name: str, value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric when present")
    return float(value)


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class AnalysisDesign(_ValueEnum):
    PAIRED = "PAIRED"
    INDEPENDENT = "INDEPENDENT"
    DESCRIPTIVE_ONLY = "DESCRIPTIVE_ONLY"


class InferenceMode(_ValueEnum):
    FREQUENTIST = "FREQUENTIST"
    BAYESIAN = "BAYESIAN"
    NONE = "NONE"


@dataclass(frozen=True)
class AnalysisPlan:
    analysis_id: str
    design: AnalysisDesign
    primary_metric: str
    secondary_metrics: tuple[str, ...]
    estimand: str
    summary_statistics: tuple[str, ...]
    inference_mode: InferenceMode
    uncertainty_method: str
    confidence_level: float | None
    analysis_population_rule: str
    missing_data_rule: str
    blocked_run_rule: str
    protocol_deviation_rule: str
    multiplicity_rule: str
    outlier_rule: str
    analysis_script_ref: str
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "analysis_id": self.analysis_id,
            "design": self.design.value,
            "primary_metric": self.primary_metric,
            "secondary_metrics": sorted(set(self.secondary_metrics)),
            "estimand": self.estimand,
            "summary_statistics": sorted(set(self.summary_statistics)),
            "inference_mode": self.inference_mode.value,
            "uncertainty_method": self.uncertainty_method,
            "confidence_level": self.confidence_level,
            "analysis_population_rule": self.analysis_population_rule,
            "missing_data_rule": self.missing_data_rule,
            "blocked_run_rule": self.blocked_run_rule,
            "protocol_deviation_rule": self.protocol_deviation_rule,
            "multiplicity_rule": self.multiplicity_rule,
            "outlier_rule": self.outlier_rule,
            "analysis_script_ref": self.analysis_script_ref,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AnalysisPlan":
        if not isinstance(value, Mapping):
            raise ValueError("analysis plan payload must be a mapping")
        schema_version = _strict_schema(value)
        return cls(
            analysis_id=_required_string("analysis_id", value.get("analysis_id")),
            design=AnalysisDesign(value["design"]),
            primary_metric=_required_string("primary_metric", value.get("primary_metric")),
            secondary_metrics=_string_tuple("secondary_metrics", value.get("secondary_metrics", ())),
            estimand=_required_string("estimand", value.get("estimand")),
            summary_statistics=_string_tuple("summary_statistics", value.get("summary_statistics", ())),
            inference_mode=InferenceMode(value["inference_mode"]),
            uncertainty_method=_required_string("uncertainty_method", value.get("uncertainty_method")),
            confidence_level=_optional_float("confidence_level", value.get("confidence_level")),
            analysis_population_rule=_required_string("analysis_population_rule", value.get("analysis_population_rule")),
            missing_data_rule=_required_string("missing_data_rule", value.get("missing_data_rule")),
            blocked_run_rule=_required_string("blocked_run_rule", value.get("blocked_run_rule")),
            protocol_deviation_rule=_required_string("protocol_deviation_rule", value.get("protocol_deviation_rule")),
            multiplicity_rule=_required_string("multiplicity_rule", value.get("multiplicity_rule")),
            outlier_rule=_required_string("outlier_rule", value.get("outlier_rule")),
            analysis_script_ref=_required_string("analysis_script_ref", value.get("analysis_script_ref")),
            schema_version=schema_version,
        )

    @classmethod
    def from_json(cls, value: str) -> "AnalysisPlan":
        return cls.from_dict(json.loads(value))


@dataclass(frozen=True)
class FrozenAnalysisPlan:
    analysis_plan: AnalysisPlan
    content_hash: str
    study_spec_hash: str
    freeze_schema_version: int = FREEZE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "freeze_schema_version": self.freeze_schema_version,
            "content_hash": self.content_hash,
            "study_spec_hash": self.study_spec_hash,
            "analysis_plan": self.analysis_plan.to_dict(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _required(name: str, value: str, issues: list[str]) -> None:
    if not value.strip():
        issues.append(f"{name} must be non-empty")


def validate_analysis_plan(plan: AnalysisPlan) -> tuple[str, ...]:
    issues: list[str] = []
    for name in (
        "analysis_id",
        "primary_metric",
        "estimand",
        "uncertainty_method",
        "analysis_population_rule",
        "missing_data_rule",
        "blocked_run_rule",
        "protocol_deviation_rule",
        "multiplicity_rule",
        "outlier_rule",
        "analysis_script_ref",
    ):
        _required(name, str(getattr(plan, name)), issues)

    if not plan.summary_statistics:
        issues.append("summary_statistics must contain at least one declared statistic")
    if plan.primary_metric in plan.secondary_metrics:
        issues.append("primary_metric must not be duplicated in secondary_metrics")

    if plan.inference_mode is InferenceMode.FREQUENTIST:
        if plan.confidence_level is None or not (0.0 < plan.confidence_level < 1.0):
            issues.append("FREQUENTIST analysis requires confidence_level strictly between 0 and 1")
    elif plan.inference_mode is InferenceMode.NONE:
        if plan.confidence_level is not None:
            issues.append("DESCRIPTIVE inference must not declare a confidence_level")

    if plan.design is AnalysisDesign.DESCRIPTIVE_ONLY and plan.inference_mode is not InferenceMode.NONE:
        issues.append("DESCRIPTIVE_ONLY design requires inference_mode NONE")

    return tuple(sorted(set(issues)))


def validate_analysis_compatibility(plan: AnalysisPlan, study: StudySpec) -> tuple[str, ...]:
    issues = list(validate_analysis_plan(plan))
    if plan.primary_metric != study.primary_metric:
        issues.append("analysis primary_metric must match frozen Study Spec primary_metric")
    undeclared = set(plan.secondary_metrics) - set(study.metrics)
    if undeclared:
        issues.append(f"analysis contains undeclared secondary metrics: {sorted(undeclared)}")
    return tuple(sorted(set(issues)))


def freeze_analysis_plan(plan: AnalysisPlan, study: FrozenStudySpec) -> FrozenAnalysisPlan:
    canonical = freeze_study_spec(study.study_spec)
    if canonical.content_hash != study.content_hash:
        raise ValueError("frozen Study Spec hash does not match Study Spec content")
    issues = validate_analysis_compatibility(plan, study.study_spec)
    if issues:
        raise ValueError("Invalid analysis plan: " + "; ".join(issues))
    identity = json.dumps(
        {"analysis_plan": plan.to_dict(), "study_spec_hash": study.content_hash},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return FrozenAnalysisPlan(
        analysis_plan=plan,
        content_hash=f"sha256:{digest}",
        study_spec_hash=study.content_hash,
    )
