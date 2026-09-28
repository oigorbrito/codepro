"""Independent acceptance decisions after governed verification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .spine import GovernedExecutionRecord, SpineStatus
from .verification import PatchVerificationStatus


class AcceptanceStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    INDETERMINATE = "INDETERMINATE"
    BLOCKED = "BLOCKED"
    NOT_EXECUTED = "NOT_EXECUTED"


class AcceptanceReason(str, Enum):
    VERIFIED = "VERIFIED"
    VERIFICATION_REJECTED = "VERIFICATION_REJECTED"
    VERIFICATION_UNKNOWN = "VERIFICATION_UNKNOWN"
    EXECUTION_BLOCKED = "EXECUTION_BLOCKED"
    NOT_EXECUTED = "NOT_EXECUTED"
    AUTHORITY_MISMATCH = "AUTHORITY_MISMATCH"
    AUTHORITY_NOT_INDEPENDENT = "AUTHORITY_NOT_INDEPENDENT"
    EVIDENCE_REQUIRED = "EVIDENCE_REQUIRED"


@dataclass(frozen=True)
class AcceptanceAuthority:
    authority_ref: str
    independent_of_executor: bool
    identity_evidence_ref: str

    def __post_init__(self) -> None:
        if not self.authority_ref.strip() or not self.identity_evidence_ref.strip():
            raise ValueError("acceptance authority identity and evidence must be explicit")
        if not isinstance(self.independent_of_executor, bool):
            raise ValueError("independent_of_executor must be boolean")


@dataclass(frozen=True)
class AcceptanceDecision:
    status: AcceptanceStatus
    reason: AcceptanceReason
    authority_ref: str
    run_id: str
    execution_artifact_ref: str | None
    verification_ref: str | None
    evidence_refs: tuple[str, ...]
    rationale: str

    def __post_init__(self) -> None:
        if not self.authority_ref.strip() or not self.run_id.strip():
            raise ValueError("authority_ref and run_id must be explicit")
        if any(not ref.strip() for ref in self.evidence_refs):
            raise ValueError("evidence_refs cannot contain blanks")
        if self.status is AcceptanceStatus.ACCEPTED and not self.evidence_refs:
            raise ValueError("ACCEPTED requires evidence_refs")

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "reason": self.reason.value,
            "authority_ref": self.authority_ref,
            "run_id": self.run_id,
            "execution_artifact_ref": self.execution_artifact_ref,
            "verification_ref": self.verification_ref,
            "evidence_refs": list(self.evidence_refs),
            "rationale": self.rationale,
        }


def decide_acceptance(
    record: GovernedExecutionRecord,
    authority: AcceptanceAuthority,
    *,
    run_id: str,
    execution_artifact_ref: str | None,
    verification_ref: str | None,
    evidence_refs: tuple[str, ...],
    rationale: str,
) -> AcceptanceDecision:
    """Make an independent, auditable decision without promoting anything."""

    if not run_id.strip():
        raise ValueError("run_id must be explicit")

    if record.acceptance_authority_ref != authority.authority_ref:
        return _decision(AcceptanceStatus.BLOCKED, AcceptanceReason.AUTHORITY_MISMATCH, run_id, authority, execution_artifact_ref, verification_ref, evidence_refs, rationale)
    if not authority.independent_of_executor:
        return _decision(AcceptanceStatus.BLOCKED, AcceptanceReason.AUTHORITY_NOT_INDEPENDENT, run_id, authority, execution_artifact_ref, verification_ref, evidence_refs, rationale)
    if not evidence_refs:
        return _decision(AcceptanceStatus.BLOCKED, AcceptanceReason.EVIDENCE_REQUIRED, run_id, authority, execution_artifact_ref, verification_ref, evidence_refs, rationale)
    if record.status is SpineStatus.READY_FOR_ACCEPTANCE:
        if record.verification is None or record.verification.status is not PatchVerificationStatus.VERIFIED:
            return _decision(AcceptanceStatus.INDETERMINATE, AcceptanceReason.VERIFICATION_UNKNOWN, run_id, authority, execution_artifact_ref, verification_ref, evidence_refs, rationale)
        if not execution_artifact_ref or not verification_ref:
            return _decision(AcceptanceStatus.BLOCKED, AcceptanceReason.EVIDENCE_REQUIRED, run_id, authority, execution_artifact_ref, verification_ref, evidence_refs, rationale)
        return _decision(AcceptanceStatus.ACCEPTED, AcceptanceReason.VERIFIED, run_id, authority, execution_artifact_ref, verification_ref, evidence_refs, rationale)
    if record.status is SpineStatus.REJECTED:
        return _decision(AcceptanceStatus.REJECTED, AcceptanceReason.VERIFICATION_REJECTED, run_id, authority, execution_artifact_ref, verification_ref, evidence_refs, rationale)
    if record.status is SpineStatus.BLOCKED:
        return _decision(AcceptanceStatus.BLOCKED, AcceptanceReason.EXECUTION_BLOCKED, run_id, authority, execution_artifact_ref, verification_ref, evidence_refs, rationale)
    if record.status is SpineStatus.UNKNOWN:
        return _decision(AcceptanceStatus.INDETERMINATE, AcceptanceReason.VERIFICATION_UNKNOWN, run_id, authority, execution_artifact_ref, verification_ref, evidence_refs, rationale)
    if record.invocation_state.value == "NOT_EXECUTED":
        return _decision(AcceptanceStatus.NOT_EXECUTED, AcceptanceReason.NOT_EXECUTED, run_id, authority, execution_artifact_ref, verification_ref, evidence_refs, rationale)
    return _decision(AcceptanceStatus.INDETERMINATE, AcceptanceReason.VERIFICATION_UNKNOWN, run_id, authority, execution_artifact_ref, verification_ref, evidence_refs, rationale)


def _decision(status, reason, run_id, authority, execution_artifact_ref, verification_ref, evidence_refs, rationale):
    return AcceptanceDecision(status, reason, authority.authority_ref, run_id, execution_artifact_ref, verification_ref, tuple(evidence_refs), rationale)
