"""Bounded, rule-based routing and escalation policy for P3.

The policy produces decisions only. A future layer may execute a decision;
this module does not know concrete executors and never produces PASS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Any

from .characterization import Confidence, RecommendedPath, Scope, TaskCharacterization
from .progress import ProgressAssessment, ProgressStatus


SCHEMA_VERSION = 1
POLICY_VERSION = "p3.rule-based.v1"


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class RoutingDecisionType(_ValueEnum):
    ROUTE = "ROUTE"
    REQUIRE_QUALIFICATION = "REQUIRE_QUALIFICATION"
    REJECT_INVALID_INPUT = "REJECT_INVALID_INPUT"


class EscalationAction(_ValueEnum):
    CONTINUE = "CONTINUE"
    STOP_SUFFICIENT_EVIDENCE = "STOP_SUFFICIENT_EVIDENCE"
    ESCALATE = "ESCALATE"
    BLOCK = "BLOCK"
    REQUIRE_QUALIFICATION = "REQUIRE_QUALIFICATION"


class EvidenceSufficiency(_ValueEnum):
    SUFFICIENT = "SUFFICIENT"
    INSUFFICIENT = "INSUFFICIENT"
    UNKNOWN = "UNKNOWN"


class ReasonCode(_ValueEnum):
    CHARACTERIZED_SIMPLE = "CHARACTERIZED_SIMPLE"
    CHARACTERIZED_LOCALIZED = "CHARACTERIZED_LOCALIZED"
    CHARACTERIZED_REPOSITORY_WIDE = "CHARACTERIZED_REPOSITORY_WIDE"
    CHARACTERIZATION_UNCERTAIN = "CHARACTERIZATION_UNCERTAIN"
    PROGRESS_CONFIRMED = "PROGRESS_CONFIRMED"
    NO_PROGRESS_DETECTED = "NO_PROGRESS_DETECTED"
    PROGRESS_UNKNOWN = "PROGRESS_UNKNOWN"
    EVIDENCE_SUFFICIENT = "EVIDENCE_SUFFICIENT"
    EVIDENCE_INSUFFICIENT = "EVIDENCE_INSUFFICIENT"
    EVIDENCE_UNKNOWN = "EVIDENCE_UNKNOWN"
    ESCALATION_BUDGET_AVAILABLE = "ESCALATION_BUDGET_AVAILABLE"
    ESCALATION_BUDGET_EXHAUSTED = "ESCALATION_BUDGET_EXHAUSTED"
    ATTEMPT_BUDGET_AVAILABLE = "ATTEMPT_BUDGET_AVAILABLE"
    ATTEMPT_BUDGET_EXHAUSTED = "ATTEMPT_BUDGET_EXHAUSTED"
    NO_HIGHER_PATH = "NO_HIGHER_PATH"
    INVALID_PATH_TRANSITION = "INVALID_PATH_TRANSITION"
    INVALID_CHARACTERIZATION = "INVALID_CHARACTERIZATION"


PATH_LADDER: tuple[RecommendedPath, ...] = (
    RecommendedPath.SIMPLE_PATH,
    RecommendedPath.LOCALIZED_PATH,
    RecommendedPath.REPOSITORY_WIDE_PATH,
)


@dataclass(frozen=True)
class RoutingBudget:
    max_path_escalations: int = 2
    max_attempts: int = 3

    def to_dict(self) -> dict[str, int]:
        return {
            "max_path_escalations": self.max_path_escalations,
            "max_attempts": self.max_attempts,
        }


@dataclass(frozen=True)
class BudgetState:
    budget: RoutingBudget = field(default_factory=RoutingBudget)
    attempts_used: int = 0
    path_escalations_used: int = 0

    @property
    def attempts_available(self) -> bool:
        return self.attempts_used < self.budget.max_attempts

    @property
    def escalation_available(self) -> bool:
        return self.path_escalations_used < self.budget.max_path_escalations

    def after(self, action: EscalationAction) -> "BudgetState":
        if action is EscalationAction.ESCALATE:
            return BudgetState(
                budget=self.budget,
                attempts_used=self.attempts_used,
                path_escalations_used=self.path_escalations_used + 1,
            )
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.budget.to_dict(),
            "attempts_used": self.attempts_used,
            "path_escalations_used": self.path_escalations_used,
        }


@dataclass(frozen=True)
class RoutingDecision:
    schema_version: int
    task_id: str
    initial_path: RecommendedPath | None
    selected_path: RecommendedPath | None
    decision: RoutingDecisionType
    confidence: Confidence
    reason_codes: tuple[ReasonCode, ...]
    characterization_ref: str | None
    policy_version: str
    budget: BudgetState
    telemetry: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "initial_path": None if self.initial_path is None else self.initial_path.value,
            "selected_path": None if self.selected_path is None else self.selected_path.value,
            "decision": self.decision.value,
            "confidence": self.confidence.value,
            "reason_codes": [code.value for code in self.reason_codes],
            "characterization_ref": self.characterization_ref,
            "policy_version": self.policy_version,
            "budget": self.budget.to_dict(),
            "telemetry": self.telemetry,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class EscalationDecision:
    schema_version: int
    current_path: RecommendedPath | None
    action: EscalationAction
    target_path: RecommendedPath | None
    reason_codes: tuple[ReasonCode, ...]
    progress_status: ProgressStatus
    evidence_sufficiency: EvidenceSufficiency
    budget_state: BudgetState
    telemetry: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "current_path": None if self.current_path is None else self.current_path.value,
            "action": self.action.value,
            "target_path": None if self.target_path is None else self.target_path.value,
            "reason_codes": [code.value for code in self.reason_codes],
            "progress_status": self.progress_status.value,
            "evidence_sufficiency": self.evidence_sufficiency.value,
            "budget_state": self.budget_state.to_dict(),
            "telemetry": self.telemetry,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def route_characterization(
    task_id: str,
    characterization: TaskCharacterization | None,
    *,
    budget_state: BudgetState | None = None,
    characterization_ref: str | None = None,
) -> RoutingDecision:
    """Map P1's closed classification to a path without hidden inference."""

    budget_state = budget_state or BudgetState()
    if characterization is None:
        return _routing(
            task_id=task_id,
            initial_path=None,
            selected_path=None,
            decision=RoutingDecisionType.REQUIRE_QUALIFICATION,
            confidence=Confidence.LOW,
            reason_codes=(ReasonCode.CHARACTERIZATION_UNCERTAIN,),
            characterization_ref=characterization_ref,
            budget=budget_state,
        )

    expected = {
        Scope.SIMPLE: RecommendedPath.SIMPLE_PATH,
        Scope.LOCALIZED: RecommendedPath.LOCALIZED_PATH,
        Scope.REPOSITORY_WIDE: RecommendedPath.REPOSITORY_WIDE_PATH,
        Scope.UNKNOWN: RecommendedPath.QUALIFICATION_REQUIRED,
    }[characterization.scope]
    if expected is RecommendedPath.QUALIFICATION_REQUIRED:
        return _routing(
            task_id=task_id,
            initial_path=expected,
            selected_path=expected,
            decision=RoutingDecisionType.REQUIRE_QUALIFICATION,
            confidence=Confidence.LOW,
            reason_codes=(ReasonCode.CHARACTERIZATION_UNCERTAIN,),
            characterization_ref=characterization_ref,
            budget=budget_state,
        )
    if characterization.recommended_path is not expected:
        return _routing(
            task_id=task_id,
            initial_path=expected,
            selected_path=None,
            decision=RoutingDecisionType.REJECT_INVALID_INPUT,
            confidence=Confidence.LOW,
            reason_codes=(ReasonCode.INVALID_CHARACTERIZATION,),
            characterization_ref=characterization_ref,
            budget=budget_state,
        )

    reason = {
        Scope.SIMPLE: ReasonCode.CHARACTERIZED_SIMPLE,
        Scope.LOCALIZED: ReasonCode.CHARACTERIZED_LOCALIZED,
        Scope.REPOSITORY_WIDE: ReasonCode.CHARACTERIZED_REPOSITORY_WIDE,
    }[characterization.scope]
    return _routing(
        task_id=task_id,
        initial_path=expected,
        selected_path=expected,
        decision=RoutingDecisionType.ROUTE,
        confidence=characterization.confidence,
        reason_codes=(reason,),
        characterization_ref=characterization_ref,
        budget=budget_state,
    )


def _routing(**values: Any) -> RoutingDecision:
    decision = values["decision"]
    return RoutingDecision(
        schema_version=SCHEMA_VERSION,
        policy_version=POLICY_VERSION,
        telemetry={
            "initial_path": None if values["initial_path"] is None else values["initial_path"].value,
            "selected_path": None if values["selected_path"] is None else values["selected_path"].value,
            "routing_decision": decision.value,
            "escalation_action": None,
            "escalation_count": values["budget"].path_escalations_used,
            "attempt_count": values["budget"].attempts_used,
            "routing_reason_codes": [code.value for code in values["reason_codes"]],
        },
        **values,
    )


def _next_path(path: RecommendedPath | None) -> RecommendedPath | None:
    if path not in PATH_LADDER:
        return None
    index = PATH_LADDER.index(path)
    return PATH_LADDER[index + 1] if index + 1 < len(PATH_LADDER) else None


def assess_escalation(
    current_path: RecommendedPath | None,
    progress: ProgressAssessment,
    evidence: EvidenceSufficiency,
    *,
    budget_state: BudgetState | None = None,
) -> EscalationDecision:
    """Produce a bounded action proposal; never execute the proposal."""

    budget_state = budget_state or BudgetState()
    reasons: list[ReasonCode] = []
    target_path: RecommendedPath | None = None

    if current_path not in PATH_LADDER:
        reasons.append(ReasonCode.INVALID_PATH_TRANSITION)
        return _escalation(current_path, EscalationAction.BLOCK, target_path, reasons, progress, evidence, budget_state)

    if evidence is EvidenceSufficiency.SUFFICIENT and progress.status is ProgressStatus.PROGRESS_PROVEN:
        reasons.extend((ReasonCode.PROGRESS_CONFIRMED, ReasonCode.EVIDENCE_SUFFICIENT))
        return _escalation(current_path, EscalationAction.STOP_SUFFICIENT_EVIDENCE, current_path, reasons, progress, evidence, budget_state)

    if evidence is EvidenceSufficiency.UNKNOWN:
        reasons.append(ReasonCode.EVIDENCE_UNKNOWN)
        return _escalation(current_path, EscalationAction.REQUIRE_QUALIFICATION, target_path, reasons, progress, evidence, budget_state)
    if progress.status is ProgressStatus.UNKNOWN:
        reasons.append(ReasonCode.PROGRESS_UNKNOWN)
        return _escalation(current_path, EscalationAction.REQUIRE_QUALIFICATION, target_path, reasons, progress, evidence, budget_state)

    if evidence is EvidenceSufficiency.SUFFICIENT:
        reasons.append(ReasonCode.EVIDENCE_SUFFICIENT)
    else:
        reasons.append(ReasonCode.EVIDENCE_INSUFFICIENT)

    if progress.status is ProgressStatus.NO_PROGRESS:
        target_path = _next_path(current_path)
        if target_path is None:
            reasons.append(ReasonCode.NO_HIGHER_PATH)
            return _escalation(current_path, EscalationAction.BLOCK, target_path, reasons, progress, evidence, budget_state)
        if not budget_state.escalation_available:
            reasons.append(ReasonCode.ESCALATION_BUDGET_EXHAUSTED)
            return _escalation(current_path, EscalationAction.BLOCK, target_path, reasons, progress, evidence, budget_state)
        reasons.extend((ReasonCode.NO_PROGRESS_DETECTED, ReasonCode.ESCALATION_BUDGET_AVAILABLE))
        return _escalation(current_path, EscalationAction.ESCALATE, target_path, reasons, progress, evidence, budget_state)

    if progress.status is ProgressStatus.PROGRESS_PROVEN:
        reasons.append(ReasonCode.PROGRESS_CONFIRMED)
    if not budget_state.attempts_available:
        reasons.append(ReasonCode.ATTEMPT_BUDGET_EXHAUSTED)
        return _escalation(current_path, EscalationAction.BLOCK, target_path, reasons, progress, evidence, budget_state)
    reasons.append(ReasonCode.ATTEMPT_BUDGET_AVAILABLE)
    return _escalation(current_path, EscalationAction.CONTINUE, current_path, reasons, progress, evidence, budget_state)


def _escalation(current_path, action, target_path, reasons, progress, evidence, budget_state):
    result_state = budget_state.after(action)
    codes = tuple(dict.fromkeys(reasons))
    return EscalationDecision(
        schema_version=SCHEMA_VERSION,
        current_path=current_path,
        action=action,
        target_path=target_path,
        reason_codes=codes,
        progress_status=progress.status,
        evidence_sufficiency=evidence,
        budget_state=result_state,
        telemetry={
            "initial_path": None if current_path is None else current_path.value,
            "selected_path": None if target_path is None else target_path.value,
            "routing_decision": None,
            "escalation_action": action.value,
            "escalation_count": result_state.path_escalations_used,
            "attempt_count": result_state.attempts_used,
            "routing_reason_codes": [code.value for code in codes],
        },
    )
