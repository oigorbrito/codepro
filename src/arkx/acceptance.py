"""Independent acceptance boundary for verified execution artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .outcomes import AcceptanceDecision, AcceptanceResult, VerificationResult, VerificationState


@dataclass(frozen=True)
class AcceptancePolicy:
    identity: str
    require_verification_evidence: bool = True
    require_verification_authority: bool = True

    def __post_init__(self) -> None:
        if not self.identity:
            raise ValueError("acceptance authority identity must be explicit")


def decide_independent_acceptance(verification: VerificationResult, policy: AcceptancePolicy) -> AcceptanceResult:
    """Map verification to acceptance only under an explicit independent policy."""

    evidence = tuple(sorted(set((verification.reference,) + verification.evidence)))

    if policy.require_verification_authority and not verification.authority:
        return AcceptanceResult(AcceptanceDecision.BLOCKED, policy.identity, "verification authority missing", evidence)
    if policy.require_verification_evidence and not verification.evidence:
        return AcceptanceResult(AcceptanceDecision.BLOCKED, policy.identity, "verification evidence missing", evidence)
    mapping = {
        VerificationState.PASS: AcceptanceDecision.ACCEPTED,
        VerificationState.FAIL: AcceptanceDecision.REJECTED,
        VerificationState.INDETERMINATE: AcceptanceDecision.INDETERMINATE,
        VerificationState.NOT_EXECUTED: AcceptanceDecision.NOT_EXECUTED,
        VerificationState.BLOCKED: AcceptanceDecision.BLOCKED,
    }
    return AcceptanceResult(mapping[verification.state], policy.identity, verification.state.value, evidence)
