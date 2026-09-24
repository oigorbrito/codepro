"""Predeclared promotion gates and explicit promotion decisions for CodePro."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from math import isfinite
from typing import Any, Mapping

from .acceptance import AcceptanceDecision, AcceptanceStatus


SCHEMA_VERSION = 1
FREEZE_SCHEMA_VERSION = 1


def _strict_schema(value: Mapping[str, Any]) -> int:
    raw = value.get("schema_version", 0)
    if isinstance(raw, bool) or not isinstance(raw, int) or raw != SCHEMA_VERSION:
        raise ValueError(f"Unsupported promotion gate schema: {raw}")
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


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class CriterionOperator(_ValueEnum):
    GTE = "GTE"
    LTE = "LTE"
    EQ = "EQ"


class GateStatus(_ValueEnum):
    ELIGIBLE_FOR_REVIEW = "ELIGIBLE_FOR_REVIEW"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    BLOCKED = "BLOCKED"


class PromotionDecisionStatus(_ValueEnum):
    PROMOTED = "PROMOTED"
    NOT_PROMOTED = "NOT_PROMOTED"


Scalar = bool | int | float | str


@dataclass(frozen=True)
class PromotionCriterion:
    criterion_id: str
    observation_key: str
    operator: CriterionOperator
    target: Scalar
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "criterion_id": self.criterion_id,
            "observation_key": self.observation_key,
            "operator": self.operator.value,
            "target": self.target,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "PromotionCriterion":
        if not isinstance(value, Mapping):
            raise ValueError("promotion criterion must be a mapping")
        target = value.get("target")
        if not isinstance(target, (bool, int, float, str)):
            raise ValueError("criterion target must be a scalar")
        if isinstance(target, float) and not isfinite(target):
            raise ValueError("criterion target must be finite")
        return cls(
            criterion_id=_required_string("criterion_id", value.get("criterion_id")),
            observation_key=_required_string("observation_key", value.get("observation_key")),
            operator=CriterionOperator(value["operator"]),
            target=target,
            rationale=_required_string("rationale", value.get("rationale")),
        )


@dataclass(frozen=True)
class PromotionGate:
    gate_id: str
    criteria: tuple[PromotionCriterion, ...]
    required_evidence_keys: tuple[str, ...]
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "gate_id": self.gate_id,
            "criteria": [
                item.to_dict() for item in sorted(self.criteria, key=lambda x: x.criterion_id)
            ],
            "required_evidence_keys": sorted(set(self.required_evidence_keys)),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "PromotionGate":
        if not isinstance(value, Mapping):
            raise ValueError("promotion gate payload must be a mapping")
        schema_version = _strict_schema(value)
        criteria = value.get("criteria", ())
        if not isinstance(criteria, (list, tuple)):
            raise ValueError("criteria must be a list or tuple")
        return cls(
            gate_id=_required_string("gate_id", value.get("gate_id")),
            criteria=tuple(PromotionCriterion.from_dict(item) for item in criteria),
            required_evidence_keys=_string_tuple("required_evidence_keys", value.get("required_evidence_keys", ())),
            schema_version=schema_version,
        )


@dataclass(frozen=True)
class FrozenPromotionGate:
    gate: PromotionGate
    content_hash: str
    freeze_schema_version: int = FREEZE_SCHEMA_VERSION

    def to_json(self) -> str:
        payload = {
            "freeze_schema_version": self.freeze_schema_version,
            "content_hash": self.content_hash,
            "gate": self.gate.to_dict(),
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


@dataclass(frozen=True)
class CriterionAssessment:
    criterion_id: str
    satisfied: bool | None
    observed: Scalar | None
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "criterion_id": self.criterion_id,
            "satisfied": self.satisfied,
            "observed": self.observed,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class GateAssessment:
    gate_id: str
    gate_hash: str
    status: GateStatus
    criteria: tuple[CriterionAssessment, ...]
    missing_evidence_keys: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "gate_hash": self.gate_hash,
            "status": self.status.value,
            "criteria": [item.to_dict() for item in self.criteria],
            "missing_evidence_keys": list(self.missing_evidence_keys),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @property
    def content_hash(self) -> str:
        digest = hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()
        return f"sha256:{digest}"


@dataclass(frozen=True)
class PromotionRecord:
    gate_hash: str
    gate_assessment_hash: str
    decision: PromotionDecisionStatus
    reviewer: str
    rationale: str
    evidence_refs: tuple[str, ...]
    acceptance_ref: str | None = None
    acceptance_run_id: str | None = None
    acceptance_authority_ref: str | None = None
    acceptance_evidence_refs: tuple[str, ...] = ()
    component_ref: str | None = None
    path_refs: tuple[str, ...] = ()
    configuration_ref: str | None = None
    study_evidence_refs: tuple[str, ...] = ()

    def to_json(self) -> str:
        payload = {
            "gate_hash": self.gate_hash,
            "gate_assessment_hash": self.gate_assessment_hash,
            "decision": self.decision.value,
            "reviewer": self.reviewer,
            "rationale": self.rationale,
            "evidence_refs": sorted(set(self.evidence_refs)),
            "acceptance_ref": self.acceptance_ref,
            "acceptance_run_id": self.acceptance_run_id,
            "acceptance_authority_ref": self.acceptance_authority_ref,
            "acceptance_evidence_refs": sorted(set(self.acceptance_evidence_refs)),
            "component_ref": self.component_ref,
            "path_refs": sorted(set(self.path_refs)),
            "configuration_ref": self.configuration_ref,
            "study_evidence_refs": sorted(set(self.study_evidence_refs)),
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def validate_promotion_gate(gate: PromotionGate) -> tuple[str, ...]:
    issues: list[str] = []
    if not gate.gate_id.strip():
        issues.append("gate_id must be non-empty")
    if not gate.criteria:
        issues.append("promotion gate requires at least one criterion")
    ids = [item.criterion_id for item in gate.criteria]
    if len(set(ids)) != len(ids):
        issues.append("criterion_id values must be unique")
    keys = [item.observation_key for item in gate.criteria]
    if len(set(keys)) != len(keys):
        issues.append("observation_key values must be unique within one gate")

    for criterion in gate.criteria:
        if not criterion.criterion_id.strip():
            issues.append("criterion_id must be non-empty")
        if not criterion.observation_key.strip():
            issues.append("observation_key must be non-empty")
        if not criterion.rationale.strip():
            issues.append(f"criterion {criterion.criterion_id!r} requires rationale")
        if criterion.operator in (CriterionOperator.GTE, CriterionOperator.LTE):
            if isinstance(criterion.target, bool) or not isinstance(criterion.target, (int, float)):
                issues.append(
                    f"criterion {criterion.criterion_id!r} numeric operator requires numeric target"
                )
            elif not isfinite(float(criterion.target)):
                issues.append(
                    f"criterion {criterion.criterion_id!r} numeric target must be finite"
                )

    if not gate.required_evidence_keys:
        issues.append("promotion gate requires explicit evidence requirements")
    if any(not key.strip() for key in gate.required_evidence_keys):
        issues.append("required_evidence_keys cannot contain blanks")

    return tuple(sorted(set(issues)))


def freeze_promotion_gate(gate: PromotionGate) -> FrozenPromotionGate:
    issues = validate_promotion_gate(gate)
    if issues:
        raise ValueError("Invalid promotion gate: " + "; ".join(issues))
    digest = hashlib.sha256(gate.to_json().encode("utf-8")).hexdigest()
    return FrozenPromotionGate(gate=gate, content_hash=f"sha256:{digest}")


def _assess(criterion: PromotionCriterion, observed: Scalar | None) -> CriterionAssessment:
    if observed is None:
        return CriterionAssessment(
            criterion_id=criterion.criterion_id,
            satisfied=None,
            observed=None,
            reason="required observation missing",
        )

    if criterion.operator is CriterionOperator.EQ:
        satisfied = observed == criterion.target
    else:
        if isinstance(observed, bool) or not isinstance(observed, (int, float)) or not isfinite(float(observed)):
            return CriterionAssessment(
                criterion_id=criterion.criterion_id,
                satisfied=None,
                observed=observed,
                reason="numeric criterion received non-finite or non-numeric observation",
            )
        target = criterion.target
        if isinstance(target, bool) or not isinstance(target, (int, float)) or not isfinite(float(target)):
            return CriterionAssessment(
                criterion_id=criterion.criterion_id,
                satisfied=None,
                observed=observed,
                reason="invalid numeric target",
            )
        satisfied = observed >= target if criterion.operator is CriterionOperator.GTE else observed <= target

    return CriterionAssessment(
        criterion_id=criterion.criterion_id,
        satisfied=satisfied,
        observed=observed,
        reason="criterion satisfied" if satisfied else "criterion not satisfied",
    )


def assess_promotion_gate(
    frozen_gate: FrozenPromotionGate,
    observations: Mapping[str, Scalar | None],
    evidence: Mapping[str, str | None],
) -> GateAssessment:
    gate = frozen_gate.gate
    canonical = freeze_promotion_gate(gate)
    if canonical.content_hash != frozen_gate.content_hash:
        raise ValueError("frozen promotion gate hash does not match gate content")
    issues = validate_promotion_gate(gate)
    if issues:
        raise ValueError("Invalid promotion gate: " + "; ".join(issues))

    assessments = tuple(
        _assess(criterion, observations.get(criterion.observation_key))
        for criterion in sorted(gate.criteria, key=lambda item: item.criterion_id)
    )
    missing_evidence = tuple(
        sorted(
            key
            for key in gate.required_evidence_keys
            if not (evidence.get(key) or "").strip()
        )
    )

    if missing_evidence or any(item.satisfied is None for item in assessments):
        status = GateStatus.BLOCKED
    elif any(item.satisfied is False for item in assessments):
        status = GateStatus.NOT_ELIGIBLE
    else:
        status = GateStatus.ELIGIBLE_FOR_REVIEW

    return GateAssessment(
        gate_id=gate.gate_id,
        gate_hash=frozen_gate.content_hash,
        status=status,
        criteria=assessments,
        missing_evidence_keys=missing_evidence,
    )


def record_promotion_decision(
    assessment: GateAssessment,
    *,
    frozen_gate: FrozenPromotionGate,
    observations: Mapping[str, Scalar | None],
    evidence: Mapping[str, str | None],
    promote: bool,
    reviewer: str,
    rationale: str,
    evidence_refs: tuple[str, ...],
    acceptance_decision: AcceptanceDecision | None = None,
    acceptance_ref: str | None = None,
    component_ref: str | None = None,
    path_refs: tuple[str, ...] = (),
    configuration_ref: str | None = None,
    study_evidence_refs: tuple[str, ...] = (),
) -> PromotionRecord:
    canonical = freeze_promotion_gate(frozen_gate.gate)
    if canonical.content_hash != frozen_gate.content_hash:
        raise ValueError("frozen promotion gate hash does not match gate content")
    if assessment.gate_id != frozen_gate.gate.gate_id or assessment.gate_hash != frozen_gate.content_hash:
        raise ValueError("promotion assessment is not bound to the supplied frozen gate")
    canonical_assessment = assess_promotion_gate(frozen_gate, observations, evidence)
    if assessment.content_hash != canonical_assessment.content_hash:
        raise ValueError("promotion assessment does not match canonical gate evaluation")
    if not reviewer.strip() or not rationale.strip():
        raise ValueError("promotion decision requires reviewer and rationale")
    if not evidence_refs or any(not ref.strip() for ref in evidence_refs):
        raise ValueError("promotion decision requires non-blank evidence references")
    if promote and assessment.status is not GateStatus.ELIGIBLE_FOR_REVIEW:
        raise ValueError("cannot promote when promotion gate is not ELIGIBLE_FOR_REVIEW")
    if promote:
        if acceptance_decision is None or acceptance_decision.status is not AcceptanceStatus.ACCEPTED:
            raise ValueError("promotion requires an ACCEPTED independent acceptance decision")
        if not acceptance_ref or not acceptance_ref.strip():
            raise ValueError("promotion requires an acceptance_ref")
        if not component_ref or not component_ref.strip():
            raise ValueError("promotion requires a component_ref")
        if not path_refs or any(not ref.strip() for ref in path_refs):
            raise ValueError("promotion requires non-blank path_refs")
        if not configuration_ref or not configuration_ref.strip():
            raise ValueError("promotion requires a configuration_ref")
        if not study_evidence_refs or any(not ref.strip() for ref in study_evidence_refs):
            raise ValueError("promotion requires study_evidence_refs")
    return PromotionRecord(
        gate_hash=frozen_gate.content_hash,
        gate_assessment_hash=assessment.content_hash,
        decision=PromotionDecisionStatus.PROMOTED if promote else PromotionDecisionStatus.NOT_PROMOTED,
        reviewer=reviewer,
        rationale=rationale,
        evidence_refs=evidence_refs,
        acceptance_ref=acceptance_ref,
        acceptance_run_id=acceptance_decision.run_id if acceptance_decision else None,
        acceptance_authority_ref=acceptance_decision.authority_ref if acceptance_decision else None,
        acceptance_evidence_refs=acceptance_decision.evidence_refs if acceptance_decision else (),
        component_ref=component_ref,
        path_refs=path_refs,
        configuration_ref=configuration_ref,
        study_evidence_refs=study_evidence_refs,
    )
