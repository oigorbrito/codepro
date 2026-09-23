"""Evidence-driven recovery decisions for stagnation and failed progress."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any

from .handoff import HandoffBudgetStatus, HandoffRecord, HandoffSummary, summarize_handoffs
from .planning import ReplanRequest, ReplanTrigger
from .progress import ProgressAssessment, ProgressStatus
from .routing import EscalationAction, EscalationDecision, RecommendedPath
from .harness import derive_attempt_id


SCHEMA_VERSION = 1


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class RecoveryAction(_ValueEnum):
    CONTINUE = "CONTINUE"
    REPLAN = "REPLAN"
    ESCALATE = "ESCALATE"
    HANDOFF = "HANDOFF"
    BLOCK = "BLOCK"


class RecoveryReason(_ValueEnum):
    PROGRESS_CONFIRMED = "PROGRESS_CONFIRMED"
    NO_PROGRESS_REQUIRES_REPLAN = "NO_PROGRESS_REQUIRES_REPLAN"
    PATH_ESCALATION_AUTHORIZED = "PATH_ESCALATION_AUTHORIZED"
    QUALIFICATION_REQUIRED = "QUALIFICATION_REQUIRED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    HANDOFF_AUTHORIZED = "HANDOFF_AUTHORIZED"
    HANDOFF_BUDGET_EXCEEDED = "HANDOFF_BUDGET_EXCEEDED"
    HANDOFF_EVIDENCE_MISSING = "HANDOFF_EVIDENCE_MISSING"
    RECOVERY_BUDGET_EXHAUSTED = "RECOVERY_BUDGET_EXHAUSTED"


@dataclass(frozen=True)
class RecoveryBudget:
    max_replans: int = 1
    max_escalations: int = 2
    max_handoffs: int = 2

    def valid(self) -> bool:
        return all(value >= 0 for value in (self.max_replans, self.max_escalations, self.max_handoffs))


@dataclass(frozen=True)
class RecoveryDecision:
    action: RecoveryAction
    reason_codes: tuple[RecoveryReason, ...]
    current_path: RecommendedPath | None
    target_path: RecommendedPath | None = None
    replan_request: ReplanRequest | None = None
    handoff_summary: HandoffSummary | None = None
    telemetry: dict[str, Any] = field(default_factory=dict)
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "action": self.action.value,
            "reason_codes": [reason.value for reason in self.reason_codes],
            "current_path": None if self.current_path is None else self.current_path.value,
            "target_path": None if self.target_path is None else self.target_path.value,
            "replan_request": None if self.replan_request is None else self.replan_request.to_dict(),
            "handoff_summary": None if self.handoff_summary is None else self.handoff_summary.to_dict(),
            "telemetry": self.telemetry,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class RecoveryPlan:
    plan_id: str
    source_attempt_id: str
    action: RecoveryAction
    reason_codes: tuple[RecoveryReason, ...]
    current_path: RecommendedPath | None
    target_path: RecommendedPath | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "source_attempt_id": self.source_attempt_id,
            "action": self.action.value,
            "reason_codes": [reason.value for reason in self.reason_codes],
            "current_path": None if self.current_path is None else self.current_path.value,
            "target_path": None if self.target_path is None else self.target_path.value,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @property
    def reference(self) -> str:
        return f"recovery://{self.plan_id}"


@dataclass(frozen=True)
class RecoveryAttemptPlan:
    trial_id: str
    source_attempt_id: str
    source_attempt_number: int
    next_attempt_id: str
    next_attempt_number: int
    configuration_digest: str
    recovery_reference: str

    def __post_init__(self) -> None:
        if not self.trial_id.strip() or not self.source_attempt_id.strip() or not self.recovery_reference.strip() or not self.configuration_digest.strip():
            raise ValueError("recovery attempt identity fields must be non-empty")
        if self.source_attempt_number < 1 or self.next_attempt_number != self.source_attempt_number + 1:
            raise ValueError("recovery attempt numbers must be consecutive and positive")
        expected_source = derive_attempt_id(trial_id=self.trial_id, attempt_number=self.source_attempt_number, configuration_digest=self.configuration_digest)
        expected_next = derive_attempt_id(trial_id=self.trial_id, attempt_number=self.next_attempt_number, configuration_digest=self.configuration_digest)
        if self.source_attempt_id != expected_source or self.next_attempt_id != expected_next:
            raise ValueError("recovery attempt identity does not match trial and configuration")

    def to_dict(self) -> dict[str, Any]:
        return {"trial_id": self.trial_id, "source_attempt_id": self.source_attempt_id, "source_attempt_number": self.source_attempt_number, "next_attempt_id": self.next_attempt_id, "next_attempt_number": self.next_attempt_number, "configuration_digest": self.configuration_digest, "recovery_reference": self.recovery_reference}


def plan_recovery_attempt(*, trial_id: str, source_attempt_id: str, source_attempt_number: int, configuration_digest: str, recovery_reference: str) -> RecoveryAttemptPlan:
    """Derive a new attempt identity without executing or selecting an executor."""
    return RecoveryAttemptPlan(
        trial_id, source_attempt_id, source_attempt_number,
        derive_attempt_id(trial_id=trial_id, attempt_number=source_attempt_number + 1, configuration_digest=configuration_digest),
        source_attempt_number + 1, configuration_digest, recovery_reference,
    )


def validate_recovery_reference(plan: RecoveryPlan, reference: str) -> None:
    if reference != plan.reference:
        raise ValueError("recovery reference does not match recovery plan")


def build_recovery_plan(source_attempt_id: str, decision: RecoveryDecision) -> RecoveryPlan:
    if not source_attempt_id.strip():
        raise ValueError("source_attempt_id must be non-empty")
    payload = json.dumps({"source_attempt_id": source_attempt_id, **decision.to_dict()}, sort_keys=True, separators=(",", ":"))
    return RecoveryPlan(
        hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16], source_attempt_id,
        decision.action, decision.reason_codes, decision.current_path, decision.target_path,
    )


def decide_recovery(
    escalation: EscalationDecision,
    progress: ProgressAssessment,
    *,
    budget: RecoveryBudget | None = None,
    replans_used: int = 0,
    escalations_used: int = 0,
    replan_request: ReplanRequest | None = None,
    handoffs: tuple[HandoffRecord, ...] = (),
) -> RecoveryDecision:
    """Convert an escalation proposal into an explicit recovery artifact."""

    budget = budget or RecoveryBudget()
    if not budget.valid() or replans_used < 0 or escalations_used < 0:
        return RecoveryDecision(RecoveryAction.BLOCK, (RecoveryReason.RECOVERY_BUDGET_EXHAUSTED,), escalation.current_path, telemetry={"invalid_budget": True})

    handoff_summary = summarize_handoffs(handoffs)
    if handoffs and handoff_summary.budget_status is HandoffBudgetStatus.BUDGET_EXCEEDED:
        return RecoveryDecision(RecoveryAction.BLOCK, (RecoveryReason.HANDOFF_BUDGET_EXCEEDED,), escalation.current_path, handoff_summary=handoff_summary)
    if handoffs and any(record.reason is None or not record.evidence_refs for record in handoffs):
        return RecoveryDecision(RecoveryAction.BLOCK, (RecoveryReason.HANDOFF_EVIDENCE_MISSING,), escalation.current_path, handoff_summary=handoff_summary)

    if escalation.action is EscalationAction.STOP_SUFFICIENT_EVIDENCE or progress.status is ProgressStatus.PROGRESS_PROVEN:
        return RecoveryDecision(RecoveryAction.CONTINUE, (RecoveryReason.PROGRESS_CONFIRMED,), escalation.current_path, escalation.current_path, handoff_summary=handoff_summary)
    if escalation.action is EscalationAction.REQUIRE_QUALIFICATION:
        return RecoveryDecision(RecoveryAction.BLOCK, (RecoveryReason.QUALIFICATION_REQUIRED,), escalation.current_path, handoff_summary=handoff_summary)
    if escalation.action is EscalationAction.BLOCK:
        return RecoveryDecision(RecoveryAction.BLOCK, (RecoveryReason.INSUFFICIENT_EVIDENCE,), escalation.current_path, escalation.target_path, handoff_summary=handoff_summary)
    if escalation.action is EscalationAction.ESCALATE:
        if escalations_used >= budget.max_escalations:
            return RecoveryDecision(RecoveryAction.BLOCK, (RecoveryReason.RECOVERY_BUDGET_EXHAUSTED,), escalation.current_path, escalation.target_path, handoff_summary=handoff_summary)
        return RecoveryDecision(RecoveryAction.ESCALATE, (RecoveryReason.PATH_ESCALATION_AUTHORIZED,), escalation.current_path, escalation.target_path, handoff_summary=handoff_summary)
    if progress.status is ProgressStatus.NO_PROGRESS:
        if replans_used >= budget.max_replans or replan_request is None:
            return RecoveryDecision(RecoveryAction.BLOCK, (RecoveryReason.RECOVERY_BUDGET_EXHAUSTED,), escalation.current_path, handoff_summary=handoff_summary)
        return RecoveryDecision(RecoveryAction.REPLAN, (RecoveryReason.NO_PROGRESS_REQUIRES_REPLAN,), escalation.current_path, escalation.target_path, replan_request, handoff_summary)
    return RecoveryDecision(RecoveryAction.CONTINUE, (RecoveryReason.PROGRESS_CONFIRMED,), escalation.current_path, escalation.current_path, handoff_summary=handoff_summary)
