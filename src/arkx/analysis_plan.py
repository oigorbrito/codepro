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
        schema_version = int(value.get("schema_version", 0))
        if schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported analysis plan schema: {schema_version}")
        return cls(
            analysis_id=str(value["analysis_id"]),
            design=AnalysisDesign(value["design"]),
            primary_metric=str(value["primary_metric"]),
            secondary_metrics=tuple(value.get("secondary_metrics", ())),
            estimand=str(value["estimand"]),
            summary_statistics=tuple(value.get("summary_statistics", ())),
            inference_mode=InferenceMode(value["inference_mode"]),
            uncertainty_method=str(value["uncertainty_method"]),
            confidence_level=value.get("confidence_level"),
            analysis_population_rule=str(value["analysis_population_rule"]),
            missing_data_rule=str(value["missing_data_rule"]),
            blocked_run_rule=str(value["blocked_run_rule"]),
            protocol_deviation_rule=str(value["protocol_deviation_rule"]),
            multiplicity_rule=str(value["multiplicity_rule"]),
            outlier_rule=str(value["outlier_rule"]),
            analysis_script_ref=str(value["analysis_script_ref"]),
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
