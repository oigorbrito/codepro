"""Fail-closed recovery decisions for the governed execution lifecycle.

The controller consumes measured progress and the existing routing policy. It
never selects an executor, silently expands scope, or performs a handoff.
Those actions require explicit caller-provided evidence and identities.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .handoff import HandoffBudgetStatus, HandoffSummary
from .characterization import RecommendedPath
from .progress import ProgressAssessment
from .routing import (
    BudgetState,
    EscalationAction,
    EvidenceSufficiency,
    assess_escalation,
)


class RecoveryAction(str, Enum):
    CONTINUE = "CONTINUE"
    REPLAN = "REPLAN"
    ESCALATE = "ESCALATE"
    HANDOFF = "HANDOFF"
    BLOCK = "BLOCK"


class RecoveryReason(str, Enum):
    PROGRESS_CONFIRMED = "PROGRESS_CONFIRMED"
    NO_PROGRESS_ESCALATION = "NO_PROGRESS_ESCALATION"
    REPLAN_REFERENCE_REQUIRED = "REPLAN_REFERENCE_REQUIRED"
    HANDOFF_EVIDENCE_REQUIRED = "HANDOFF_EVIDENCE_REQUIRED"
    HANDOFF_BUDGET_EXCEEDED = "HANDOFF_BUDGET_EXCEEDED"
    QUALIFICATION_REQUIRED = "QUALIFICATION_REQUIRED"
    RECOVERY_BUDGET_EXHAUSTED = "RECOVERY_BUDGET_EXHAUSTED"
    INVALID_REQUEST = "INVALID_REQUEST"


@dataclass(frozen=True)
class RecoveryRequest:
    """Explicit caller intent for a recovery transition."""

    action: RecoveryAction | None = None
    replan_ref: str | None = None
    previous_plan_ref: str | None = None
    target_executor_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class RecoveryDecision:
    action: RecoveryAction
    reason: RecoveryReason
    current_path: RecommendedPath | None
    target_path: RecommendedPath | None
    budget_state: BudgetState
    causal_refs: tuple[str, ...] = ()
    target_executor_ref: str | None = None
    telemetry: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "reason": self.reason.value,
            "current_path": None if self.current_path is None else self.current_path.value,
            "target_path": None if self.target_path is None else self.target_path.value,
            "budget": self.budget_state.to_dict(),
            "causal_refs": list(self.causal_refs),
            "target_executor_ref": self.target_executor_ref,
            "telemetry": self.telemetry or {},
        }


def decide_recovery(
    *,
    current_path: RecommendedPath | None,
    progress: ProgressAssessment,
    evidence: EvidenceSufficiency,
    budget_state: BudgetState | None = None,
    request: RecoveryRequest | None = None,
    handoff: HandoffSummary | None = None,
) -> RecoveryDecision:
    """Return one auditable recovery decision without performing it."""

    budget_state = budget_state or BudgetState()
    request = request or RecoveryRequest()
    proposal = assess_escalation(
        current_path,
        progress,
        evidence,
        budget_state=budget_state,
    )

    if request.action is RecoveryAction.HANDOFF:
        if not request.target_executor_ref or not request.evidence_refs or handoff is None:
            return _decision(
                RecoveryAction.BLOCK,
                RecoveryReason.HANDOFF_EVIDENCE_REQUIRED,
                current_path,
                None,
                budget_state,
            )
        if handoff.budget_status is not HandoffBudgetStatus.WITHIN_BUDGET:
            return _decision(
                RecoveryAction.BLOCK,
                RecoveryReason.HANDOFF_BUDGET_EXCEEDED,
                current_path,
                None,
                budget_state,
            )
        return _decision(
            RecoveryAction.HANDOFF,
            RecoveryReason.PROGRESS_CONFIRMED,
            current_path,
            current_path,
            budget_state,
            causal_refs=request.evidence_refs,
            target_executor_ref=request.target_executor_ref,
        )

    if request.action is RecoveryAction.REPLAN:
        refs = (request.previous_plan_ref, request.replan_ref)
        if any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            return _decision(
                RecoveryAction.BLOCK,
                RecoveryReason.REPLAN_REFERENCE_REQUIRED,
                current_path,
                None,
                budget_state,
            )
        if proposal.target_path is None or proposal.action is not EscalationAction.ESCALATE:
            return _decision(
                RecoveryAction.BLOCK,
                RecoveryReason.RECOVERY_BUDGET_EXHAUSTED,
                current_path,
                proposal.target_path,
                proposal.budget_state,
            )
        return _decision(
            RecoveryAction.REPLAN,
            RecoveryReason.NO_PROGRESS_ESCALATION,
            current_path,
            proposal.target_path,
            proposal.budget_state,
            causal_refs=tuple(refs),
        )

    if request.action is not None and request.action not in {
        RecoveryAction.CONTINUE,
        RecoveryAction.ESCALATE,
        RecoveryAction.BLOCK,
    }:
        return _decision(
            RecoveryAction.BLOCK,
            RecoveryReason.INVALID_REQUEST,
            current_path,
            None,
            budget_state,
        )

    if proposal.action is EscalationAction.CONTINUE or proposal.action is EscalationAction.STOP_SUFFICIENT_EVIDENCE:
        return _decision(
            RecoveryAction.CONTINUE,
            RecoveryReason.PROGRESS_CONFIRMED,
            current_path,
            proposal.target_path,
            proposal.budget_state,
        )
    if proposal.action is EscalationAction.ESCALATE:
        return _decision(
            RecoveryAction.ESCALATE,
            RecoveryReason.NO_PROGRESS_ESCALATION,
            current_path,
            proposal.target_path,
            proposal.budget_state,
        )
    if proposal.action is EscalationAction.REQUIRE_QUALIFICATION:
        return _decision(
            RecoveryAction.BLOCK,
            RecoveryReason.QUALIFICATION_REQUIRED,
            current_path,
            None,
            proposal.budget_state,
        )
    return _decision(
        RecoveryAction.BLOCK,
        RecoveryReason.RECOVERY_BUDGET_EXHAUSTED,
        current_path,
        proposal.target_path,
        proposal.budget_state,
    )


def _decision(action, reason, current_path, target_path, budget_state, *, causal_refs=(), target_executor_ref=None):
    return RecoveryDecision(
        action=action,
        reason=reason,
        current_path=current_path,
        target_path=target_path,
        budget_state=budget_state,
        causal_refs=tuple(causal_refs),
        target_executor_ref=target_executor_ref,
        telemetry={"recovery_action": action.value, "recovery_reason": reason.value},
    )
