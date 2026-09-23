"""Executor-neutral verification and acceptance outcome contracts.

These types belong to the product boundary.  They intentionally contain no
executor, provider, model, sandbox, or experiment-specific behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any


class VerificationState(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INDETERMINATE = "INDETERMINATE"
    NOT_EXECUTED = "NOT_EXECUTED"
    BLOCKED = "BLOCKED"


class AcceptanceDecision(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    INDETERMINATE = "INDETERMINATE"
    NOT_EXECUTED = "NOT_EXECUTED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class VerificationResult:
    state: VerificationState
    authority: str
    commands: tuple[str, ...]
    outcomes: tuple[str, ...]
    evidence: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "authority": self.authority,
            "commands": list(self.commands),
            "outcomes": list(self.outcomes),
            "evidence": list(self.evidence),
        }

    @property
    def reference(self) -> str:
        payload = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return f"verification://{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


@dataclass(frozen=True)
class AcceptanceResult:
    decision: AcceptanceDecision
    authority: str
    raw_outcome: str | None
    evidence: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "authority": self.authority,
            "raw_outcome": self.raw_outcome,
            "evidence": list(self.evidence),
        }

    @property
    def reference(self) -> str:
        payload = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return f"acceptance://{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:16]}"


def validate_outcome_references(
    verification: VerificationResult,
    acceptance: AcceptanceResult,
    *,
    verification_ref: str,
    acceptance_ref: str,
) -> None:
    if verification_ref != verification.reference:
        raise ValueError("verification reference does not match result")
    if acceptance_ref != acceptance.reference:
        raise ValueError("acceptance reference does not match result")
