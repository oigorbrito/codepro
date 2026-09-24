"""Structured protocol-deviation records for frozen Arkx empirical studies."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping


def _required_string(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _strict_bool(name: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be boolean")
    return value


SCHEMA_VERSION = 1
FREEZE_SCHEMA_VERSION = 1


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class DeviationType(_ValueEnum):
    FALLBACK = "FALLBACK"
    EXECUTOR_SWITCH = "EXECUTOR_SWITCH"
    MODEL_OR_PROVIDER_SWITCH = "MODEL_OR_PROVIDER_SWITCH"
    SCOPE_EXPANSION = "SCOPE_EXPANSION"
    TASK_SUBSTITUTION = "TASK_SUBSTITUTION"
    CONFIGURATION_CHANGE = "CONFIGURATION_CHANGE"
    RETRY_POLICY_CHANGE = "RETRY_POLICY_CHANGE"
    WORKLOAD_EXCLUSION = "WORKLOAD_EXCLUSION"
    ANALYSIS_DEVIATION = "ANALYSIS_DEVIATION"
    OTHER = "OTHER"


class DeviationPhase(_ValueEnum):
    PRE_EXECUTION_AFTER_FREEZE = "PRE_EXECUTION_AFTER_FREEZE"
    DURING_EXECUTION = "DURING_EXECUTION"
    POST_EXECUTION_ANALYSIS = "POST_EXECUTION_ANALYSIS"


class AnalysisImpact(_ValueEnum):
    NO_PRIMARY_EFFECT = "NO_PRIMARY_EFFECT"
    SENSITIVITY_ANALYSIS_REQUIRED = "SENSITIVITY_ANALYSIS_REQUIRED"
    EXCLUDE_AFFECTED_OBSERVATION = "EXCLUDE_AFFECTED_OBSERVATION"
    REQUIRES_NEW_STUDY = "REQUIRES_NEW_STUDY"
    UNKNOWN = "UNKNOWN"


_HIGH_RISK_TYPES = {
    DeviationType.FALLBACK,
    DeviationType.EXECUTOR_SWITCH,
    DeviationType.MODEL_OR_PROVIDER_SWITCH,
    DeviationType.SCOPE_EXPANSION,
    DeviationType.TASK_SUBSTITUTION,
    DeviationType.CONFIGURATION_CHANGE,
    DeviationType.RETRY_POLICY_CHANGE,
    DeviationType.WORKLOAD_EXCLUSION,
    DeviationType.ANALYSIS_DEVIATION,
}


@dataclass(frozen=True)
class ProtocolDeviation:
    deviation_id: str
    study_spec_ref: str
    scope_ref: str
    deviation_type: DeviationType
    phase: DeviationPhase
    frozen_value: str
    observed_value: str
    reason: str
    evidence_refs: tuple[str, ...]
    preauthorized_by_frozen_protocol: bool
    analysis_impact: AnalysisImpact
    impact_rationale: str
    replacement_study_spec_ref: str | None = None
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "deviation_id": self.deviation_id,
            "study_spec_ref": self.study_spec_ref,
            "scope_ref": self.scope_ref,
            "deviation_type": self.deviation_type.value,
            "phase": self.phase.value,
            "frozen_value": self.frozen_value,
            "observed_value": self.observed_value,
            "reason": self.reason,
            "evidence_refs": sorted(set(self.evidence_refs)),
            "preauthorized_by_frozen_protocol": self.preauthorized_by_frozen_protocol,
            "analysis_impact": self.analysis_impact.value,
            "impact_rationale": self.impact_rationale,
            "replacement_study_spec_ref": self.replacement_study_spec_ref,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ProtocolDeviation":
        if not isinstance(value, Mapping):
            raise ValueError("deviation payload must be a mapping")
        schema_version = value.get("schema_version", 0)
        if isinstance(schema_version, bool) or not isinstance(schema_version, int) or schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported deviation schema: {schema_version}")
        refs = value.get("evidence_refs", ())
        if not isinstance(refs, (list, tuple)):
            raise ValueError("evidence_refs must be a list or tuple")
        return cls(
            deviation_id=_required_string("deviation_id", value.get("deviation_id")),
            study_spec_ref=_required_string("study_spec_ref", value.get("study_spec_ref")),
            scope_ref=_required_string("scope_ref", value.get("scope_ref")),
            deviation_type=DeviationType(value["deviation_type"]),
            phase=DeviationPhase(value["phase"]),
            frozen_value=_required_string("frozen_value", value.get("frozen_value")),
            observed_value=_required_string("observed_value", value.get("observed_value")),
            reason=_required_string("reason", value.get("reason")),
            evidence_refs=tuple(refs),
            preauthorized_by_frozen_protocol=_strict_bool("preauthorized_by_frozen_protocol", value.get("preauthorized_by_frozen_protocol")),
            analysis_impact=AnalysisImpact(value["analysis_impact"]),
            impact_rationale=_required_string("impact_rationale", value.get("impact_rationale")),
            replacement_study_spec_ref=value.get("replacement_study_spec_ref"),
            schema_version=schema_version,
        )


@dataclass(frozen=True)
class FrozenProtocolDeviation:
    deviation: ProtocolDeviation
    content_hash: str
    freeze_schema_version: int = FREEZE_SCHEMA_VERSION

    def to_json(self) -> str:
        payload = {
            "freeze_schema_version": self.freeze_schema_version,
            "content_hash": self.content_hash,
            "deviation": self.deviation.to_dict(),
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def validate_protocol_deviation(value: ProtocolDeviation) -> tuple[str, ...]:
    issues: list[str] = []
    for name in (
        "deviation_id",
        "study_spec_ref",
        "scope_ref",
        "frozen_value",
        "observed_value",
        "reason",
        "impact_rationale",
    ):
        if not str(getattr(value, name)).strip():
            issues.append(f"{name} must be non-empty")

    if value.frozen_value == value.observed_value:
        issues.append("deviation must record an actual before/after difference")
    if not value.evidence_refs:
        issues.append("protocol deviation requires at least one evidence reference")
    elif any(not isinstance(ref, str) or not ref.strip() for ref in value.evidence_refs):
        issues.append("protocol deviation evidence references must be non-blank strings")

    if value.deviation_type in _HIGH_RISK_TYPES:
        if value.analysis_impact is AnalysisImpact.NO_PRIMARY_EFFECT and not value.preauthorized_by_frozen_protocol:
            issues.append(
                "unplanned behavior-affecting deviation cannot claim NO_PRIMARY_EFFECT without frozen preauthorization"
            )

    if value.analysis_impact is AnalysisImpact.REQUIRES_NEW_STUDY:
        if not (value.replacement_study_spec_ref or "").strip():
            issues.append("REQUIRES_NEW_STUDY requires replacement_study_spec_ref")

    return tuple(sorted(set(issues)))


def freeze_protocol_deviation(value: ProtocolDeviation) -> FrozenProtocolDeviation:
    issues = validate_protocol_deviation(value)
    if issues:
        raise ValueError("Invalid protocol deviation: " + "; ".join(issues))
    digest = hashlib.sha256(value.to_json().encode("utf-8")).hexdigest()
    return FrozenProtocolDeviation(deviation=value, content_hash=f"sha256:{digest}")
