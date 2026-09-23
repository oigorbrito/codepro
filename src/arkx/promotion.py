"""Explicit evidence-backed promotion decisions."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any

from .outcomes import AcceptanceDecision, AcceptanceResult, VerificationResult
from .harness import AttemptSnapshot, RunState, VerificationEvidence


SCHEMA_VERSION = 1


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class PromotionStatus(_ValueEnum):
    PROMOTED = "PROMOTED"
    NOT_PROMOTED = "NOT_PROMOTED"
    BLOCKED = "BLOCKED"
    INDETERMINATE = "INDETERMINATE"


class PromotionReason(_ValueEnum):
    PROMOTED_WITH_INDEPENDENT_EVIDENCE = "PROMOTED_WITH_INDEPENDENT_EVIDENCE"
    ACCEPTANCE_REQUIRED = "ACCEPTANCE_REQUIRED"
    ACCEPTANCE_AUTHORITY_MISMATCH = "ACCEPTANCE_AUTHORITY_MISMATCH"
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    EVIDENCE_INDETERMINATE = "EVIDENCE_INDETERMINATE"
    CANDIDATE_IDENTITY_MISSING = "CANDIDATE_IDENTITY_MISSING"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    VERIFICATION_EVIDENCE_MISSING = "VERIFICATION_EVIDENCE_MISSING"
    VERIFICATION_INDETERMINATE = "VERIFICATION_INDETERMINATE"
    EXECUTION_NOT_COMPLETED = "EXECUTION_NOT_COMPLETED"
    SNAPSHOT_IDENTITY_MISMATCH = "SNAPSHOT_IDENTITY_MISMATCH"
    ACCEPTANCE_VERIFICATION_MISMATCH = "ACCEPTANCE_VERIFICATION_MISMATCH"


@dataclass(frozen=True)
class PromotionCandidate:
    component_type: str
    component_id: str
    version: str | None
    configuration_digest: str | None

    def valid(self) -> bool:
        return bool(self.component_type and self.component_id)

    def to_dict(self) -> dict[str, str | None]:
        return {
            "component_type": self.component_type,
            "component_id": self.component_id,
            "version": self.version,
            "configuration_digest": self.configuration_digest,
        }


@dataclass(frozen=True)
class PromotionPolicy:
    authority_id: str
    require_acceptance: bool = True
    require_evidence: bool = True
    require_verification: bool = True

    def __post_init__(self) -> None:
        if not self.authority_id:
            raise ValueError("promotion authority_id must be explicit")


@dataclass(frozen=True)
class PromotionDecision:
    status: PromotionStatus
    reason_codes: tuple[PromotionReason, ...]
    candidate: PromotionCandidate
    authority_id: str
    acceptance: AcceptanceResult | None
    evidence_refs: tuple[str, ...]
    telemetry: dict[str, Any] = field(default_factory=dict)
    attempt_id: str | None = None
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status.value,
            "reason_codes": [reason.value for reason in self.reason_codes],
            "candidate": self.candidate.to_dict(),
            "authority_id": self.authority_id,
            "acceptance": None if self.acceptance is None else self.acceptance.to_dict(),
            "evidence_refs": list(self.evidence_refs),
            "telemetry": self.telemetry,
            "attempt_id": self.attempt_id,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @property
    def reference(self) -> str:
        payload = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return f"promotion://{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "PromotionDecision":
        acceptance_value = value.get("acceptance")
        acceptance = None if acceptance_value is None else AcceptanceResult(
            decision=AcceptanceDecision(acceptance_value["decision"]),
            authority=str(acceptance_value["authority"]),
            raw_outcome=acceptance_value.get("raw_outcome"),
            evidence=tuple(acceptance_value.get("evidence", ())),
        )
        candidate_value = value["candidate"]
        return cls(
            status=PromotionStatus(value["status"]),
            reason_codes=tuple(PromotionReason(item) for item in value.get("reason_codes", ())),
            candidate=PromotionCandidate(candidate_value["component_type"], candidate_value["component_id"], candidate_value.get("version"), candidate_value.get("configuration_digest")),
            authority_id=str(value["authority_id"]),
            acceptance=acceptance,
            evidence_refs=tuple(value.get("evidence_refs", ())),
            telemetry=dict(value.get("telemetry", {})),
            attempt_id=value.get("attempt_id"),
            schema_version=int(value.get("schema_version", 0)),
        )

    @classmethod
    def from_json(cls, value: str) -> "PromotionDecision":
        return cls.from_dict(json.loads(value))


def decide_promotion(
    candidate: PromotionCandidate,
    acceptance: AcceptanceResult | None,
    evidence_refs: tuple[str, ...] | None,
    policy: PromotionPolicy,
    verification: VerificationEvidence | None = None,
) -> PromotionDecision:
    """Promote only an explicitly identified, independently accepted candidate."""

    refs = tuple(sorted(set(evidence_refs or ())))
    if not candidate.valid():
        return PromotionDecision(PromotionStatus.BLOCKED, (PromotionReason.CANDIDATE_IDENTITY_MISSING,), candidate, policy.authority_id, acceptance, refs)
    if policy.require_verification and verification is None:
        return PromotionDecision(PromotionStatus.BLOCKED, (PromotionReason.VERIFICATION_REQUIRED,), candidate, policy.authority_id, acceptance, refs)
    if verification is not None and verification.state != "PASS":
        status = PromotionStatus.INDETERMINATE if verification.state in ("INDETERMINATE", "UNKNOWN") else PromotionStatus.NOT_PROMOTED
        reason = PromotionReason.VERIFICATION_INDETERMINATE if status is PromotionStatus.INDETERMINATE else PromotionReason.VERIFICATION_REQUIRED
        return PromotionDecision(status, (reason,), candidate, policy.authority_id, acceptance, refs)
    if policy.require_verification and verification is not None and not verification.evidence_refs:
        return PromotionDecision(PromotionStatus.BLOCKED, (PromotionReason.VERIFICATION_EVIDENCE_MISSING,), candidate, policy.authority_id, acceptance, refs)
    if policy.require_acceptance and acceptance is None:
        return PromotionDecision(PromotionStatus.BLOCKED, (PromotionReason.ACCEPTANCE_REQUIRED,), candidate, policy.authority_id, None, refs)
    if acceptance is not None and acceptance.authority != policy.authority_id:
        return PromotionDecision(PromotionStatus.BLOCKED, (PromotionReason.ACCEPTANCE_AUTHORITY_MISMATCH,), candidate, policy.authority_id, acceptance, refs)
    if acceptance is not None and acceptance.decision is AcceptanceDecision.INDETERMINATE:
        return PromotionDecision(PromotionStatus.INDETERMINATE, (PromotionReason.EVIDENCE_INDETERMINATE,), candidate, policy.authority_id, acceptance, refs)
    if acceptance is not None and acceptance.decision is not AcceptanceDecision.ACCEPTED:
        return PromotionDecision(PromotionStatus.NOT_PROMOTED, (PromotionReason.ACCEPTANCE_REQUIRED,), candidate, policy.authority_id, acceptance, refs)
    if policy.require_evidence and not refs:
        return PromotionDecision(PromotionStatus.BLOCKED, (PromotionReason.EVIDENCE_MISSING,), candidate, policy.authority_id, acceptance, refs)
    return PromotionDecision(PromotionStatus.PROMOTED, (PromotionReason.PROMOTED_WITH_INDEPENDENT_EVIDENCE,), candidate, policy.authority_id, acceptance, refs)


def decide_outcome_promotion(
    candidate: PromotionCandidate,
    verification: VerificationResult,
    acceptance: AcceptanceResult,
    evidence_refs: tuple[str, ...] | None,
    policy: PromotionPolicy,
) -> PromotionDecision:
    """Promote only when acceptance explicitly carries its verification reference."""
    if verification.reference not in acceptance.evidence:
        refs = tuple(sorted(set(evidence_refs or ())))
        return PromotionDecision(
            PromotionStatus.BLOCKED,
            (PromotionReason.ACCEPTANCE_VERIFICATION_MISMATCH,),
            candidate,
            policy.authority_id,
            acceptance,
            refs,
        )
    verification_evidence = VerificationEvidence(
        authority_identity=verification.authority,
        state=verification.state.value,
        evidence_refs=verification.evidence,
    )
    refs = tuple(sorted(set((evidence_refs or ()) + verification.evidence + (verification.reference,))))
    return decide_promotion(candidate, acceptance, refs, policy, verification_evidence)


def decide_snapshot_promotion(
    candidate: PromotionCandidate,
    snapshot: AttemptSnapshot,
    acceptance: AcceptanceResult | None,
    evidence_refs: tuple[str, ...] | None,
    policy: PromotionPolicy,
    verification: VerificationEvidence | None = None,
) -> PromotionDecision:
    """Apply promotion policy only to a validated, concrete attempt snapshot."""

    if snapshot.manifest.state is not RunState.COMPLETED:
        return PromotionDecision(PromotionStatus.BLOCKED, (PromotionReason.EXECUTION_NOT_COMPLETED,), candidate, policy.authority_id, acceptance, tuple(sorted(set(evidence_refs or ()))))
    if candidate.configuration_digest and snapshot.manifest.configuration_digest and candidate.configuration_digest != snapshot.manifest.configuration_digest:
        return PromotionDecision(PromotionStatus.BLOCKED, (PromotionReason.SNAPSHOT_IDENTITY_MISMATCH,), candidate, policy.authority_id, acceptance, tuple(sorted(set(evidence_refs or ()))))
    refs = tuple(sorted(set((evidence_refs or ()) + (() if verification is None else verification.evidence_refs))))
    decision = decide_promotion(candidate, acceptance, refs, policy, verification)
    return replace(decision, attempt_id=snapshot.manifest.attempt_id)


def write_promotion_decision(decision: PromotionDecision, path: str | Path) -> Path:
    target = Path(path)
    if target.exists():
        raise FileExistsError(f"promotion decision already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(decision.to_json() + "\n", encoding="utf-8", newline="\n")
    temporary.replace(target)
    return target


def load_promotion_decision(path: str | Path, snapshot: AttemptSnapshot) -> PromotionDecision:
    decision = PromotionDecision.from_json(Path(path).read_text(encoding="utf-8"))
    if decision.attempt_id != snapshot.manifest.attempt_id:
        raise ValueError("promotion decision attempt_id does not match snapshot")
    if decision.candidate.configuration_digest and snapshot.manifest.configuration_digest and decision.candidate.configuration_digest != snapshot.manifest.configuration_digest:
        raise ValueError("promotion decision candidate does not match snapshot configuration")
    local_refs = set(snapshot.manifest.artifact_refs)
    for reference in decision.evidence_refs:
        if reference in local_refs or reference.startswith(("evidence://", "experiment://")):
            continue
        raise ValueError(f"promotion evidence reference is not bound to snapshot: {reference}")
    return decision
