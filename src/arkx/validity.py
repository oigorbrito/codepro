"""Explicit validity argument for Arkx empirical studies."""

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


class ValidityDimension(_ValueEnum):
    CONSTRUCT = "CONSTRUCT"
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"
    CONCLUSION = "CONCLUSION"
    RELIABILITY_REPRODUCIBILITY = "RELIABILITY_REPRODUCIBILITY"


@dataclass(frozen=True)
class ConstructMapping:
    metric: str
    construct: str
    rationale: str
    limitations: str

    def to_dict(self) -> dict[str, str]:
        return {
            "metric": self.metric,
            "construct": self.construct,
            "rationale": self.rationale,
            "limitations": self.limitations,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ConstructMapping":
        return cls(
            metric=str(value["metric"]),
            construct=str(value["construct"]),
            rationale=str(value["rationale"]),
            limitations=str(value["limitations"]),
        )


@dataclass(frozen=True)
class Threat:
    threat_id: str
    dimension: ValidityDimension
    claim_at_risk: str
    mechanism: str
    mitigation: str
    residual_risk: str
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "threat_id": self.threat_id,
            "dimension": self.dimension.value,
            "claim_at_risk": self.claim_at_risk,
            "mechanism": self.mechanism,
            "mitigation": self.mitigation,
            "residual_risk": self.residual_risk,
            "evidence_refs": sorted(set(self.evidence_refs)),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Threat":
        return cls(
            threat_id=str(value["threat_id"]),
            dimension=ValidityDimension(value["dimension"]),
            claim_at_risk=str(value["claim_at_risk"]),
            mechanism=str(value["mechanism"]),
            mitigation=str(value["mitigation"]),
            residual_risk=str(value["residual_risk"]),
            evidence_refs=tuple(value.get("evidence_refs", ())),
        )


@dataclass(frozen=True)
class ValidityPlan:
    validity_id: str
    workload_refs: tuple[str, ...]
    target_population: str
    workload_representativeness_argument: str
    artifact_strengths: tuple[str, ...]
    artifact_weaknesses: tuple[str, ...]
    artifact_limitations: tuple[str, ...]
    state_of_art_alternative_refs: tuple[str, ...]
    no_alternative_justification: str | None
    construct_mappings: tuple[ConstructMapping, ...]
    threats: tuple[Threat, ...]
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "validity_id": self.validity_id,
            "workload_refs": sorted(set(self.workload_refs)),
            "target_population": self.target_population,
            "workload_representativeness_argument": self.workload_representativeness_argument,
            "artifact_strengths": sorted(set(self.artifact_strengths)),
            "artifact_weaknesses": sorted(set(self.artifact_weaknesses)),
            "artifact_limitations": sorted(set(self.artifact_limitations)),
            "state_of_art_alternative_refs": sorted(set(self.state_of_art_alternative_refs)),
            "no_alternative_justification": self.no_alternative_justification,
            "construct_mappings": [
                item.to_dict() for item in sorted(self.construct_mappings, key=lambda x: x.metric)
            ],
            "threats": [
                item.to_dict() for item in sorted(self.threats, key=lambda x: x.threat_id)
            ],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ValidityPlan":
        schema_version = int(value.get("schema_version", 0))
        if schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported validity plan schema: {schema_version}")
        return cls(
            validity_id=str(value["validity_id"]),
            workload_refs=tuple(value.get("workload_refs", ())),
            target_population=str(value["target_population"]),
            workload_representativeness_argument=str(value["workload_representativeness_argument"]),
            artifact_strengths=tuple(value.get("artifact_strengths", ())),
            artifact_weaknesses=tuple(value.get("artifact_weaknesses", ())),
            artifact_limitations=tuple(value.get("artifact_limitations", ())),
            state_of_art_alternative_refs=tuple(value.get("state_of_art_alternative_refs", ())),
            no_alternative_justification=value.get("no_alternative_justification"),
            construct_mappings=tuple(
                ConstructMapping.from_dict(item) for item in value.get("construct_mappings", ())
            ),
            threats=tuple(Threat.from_dict(item) for item in value.get("threats", ())),
            schema_version=schema_version,
        )


@dataclass(frozen=True)
class FrozenValidityPlan:
    validity_plan: ValidityPlan
    content_hash: str
    study_spec_hash: str
    freeze_schema_version: int = FREEZE_SCHEMA_VERSION

    def to_json(self) -> str:
        value = {
            "freeze_schema_version": self.freeze_schema_version,
            "content_hash": self.content_hash,
            "study_spec_hash": self.study_spec_hash,
            "validity_plan": self.validity_plan.to_dict(),
        }
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _nonempty(items: tuple[str, ...]) -> bool:
    return bool(items) and all(item.strip() for item in items)


def validate_validity_plan(plan: ValidityPlan) -> tuple[str, ...]:
    issues: list[str] = []
    for name in ("validity_id", "target_population", "workload_representativeness_argument"):
        if not str(getattr(plan, name)).strip():
            issues.append(f"{name} must be non-empty")

    if not plan.workload_refs:
        issues.append("workload_refs must contain at least one frozen workload reference")
    if not _nonempty(plan.artifact_strengths):
        issues.append("artifact_strengths must explicitly describe at least one strength")
    if not _nonempty(plan.artifact_weaknesses):
        issues.append("artifact_weaknesses must explicitly describe at least one weakness")
    if not _nonempty(plan.artifact_limitations):
        issues.append("artifact_limitations must explicitly describe at least one limitation")
    if not plan.state_of_art_alternative_refs and not (plan.no_alternative_justification or "").strip():
        issues.append("state-of-art alternatives or an explicit no-alternative justification are required")

    metrics = [mapping.metric for mapping in plan.construct_mappings]
    if len(set(metrics)) != len(metrics):
        issues.append("construct_mappings must contain at most one mapping per metric")
    for mapping in plan.construct_mappings:
        if not all((mapping.metric.strip(), mapping.construct.strip(), mapping.rationale.strip(), mapping.limitations.strip())):
            issues.append("construct mappings require metric, construct, rationale, and limitations")

    threat_ids = [threat.threat_id for threat in plan.threats]
    if len(set(threat_ids)) != len(threat_ids):
        issues.append("threat_id values must be unique")
    for threat in plan.threats:
        if not all(
            (
                threat.threat_id.strip(),
                threat.claim_at_risk.strip(),
                threat.mechanism.strip(),
                threat.mitigation.strip(),
                threat.residual_risk.strip(),
            )
        ):
            issues.append("each threat must link claim, mechanism, mitigation, and residual risk")

    required_dimensions = {
        ValidityDimension.CONSTRUCT,
        ValidityDimension.EXTERNAL,
        ValidityDimension.CONCLUSION,
        ValidityDimension.RELIABILITY_REPRODUCIBILITY,
    }
    observed_dimensions = {threat.dimension for threat in plan.threats}
    missing = required_dimensions - observed_dimensions
    if missing:
        issues.append(f"missing required validity dimensions: {sorted(item.value for item in missing)}")

    return tuple(sorted(set(issues)))


def validate_validity_compatibility(plan: ValidityPlan, study: StudySpec) -> tuple[str, ...]:
    issues = list(validate_validity_plan(plan))
    if set(plan.workload_refs) != set(study.workload_refs):
        issues.append("validity workload_refs must match frozen Study Spec workload_refs")
    mapped_metrics = {mapping.metric for mapping in plan.construct_mappings}
    missing_metrics = set(study.metrics) - mapped_metrics
    if missing_metrics:
        issues.append(f"missing construct mapping for study metrics: {sorted(missing_metrics)}")
    return tuple(sorted(set(issues)))


def freeze_validity_plan(plan: ValidityPlan, study: FrozenStudySpec) -> FrozenValidityPlan:
    canonical = freeze_study_spec(study.study_spec)
    if canonical.content_hash != study.content_hash:
        raise ValueError("frozen Study Spec hash does not match Study Spec content")
    issues = validate_validity_compatibility(plan, study.study_spec)
    if issues:
        raise ValueError("Invalid validity plan: " + "; ".join(issues))
    identity = json.dumps(
        {"validity_plan": plan.to_dict(), "study_spec_hash": study.content_hash},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return FrozenValidityPlan(
        validity_plan=plan,
        content_hash=f"sha256:{digest}",
        study_spec_hash=study.content_hash,
    )
