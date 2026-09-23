"""Request and governance contracts for the pre-characterization boundary.

Governance authorizes the conditions under which a request may be analyzed.
It does not characterize the task, select an executor, verify a patch, or
accept a result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Any

from .characterization import CharacterizationConfig, TaskCharacterization, TaskSignals, characterize


SCHEMA_VERSION = 1


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class GovernanceStatus(_ValueEnum):
    AUTHORIZED = "AUTHORIZED"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class GovernanceReason(_ValueEnum):
    AUTHORIZED = "AUTHORIZED"
    REQUEST_ID_MISSING = "REQUEST_ID_MISSING"
    TASK_ID_MISSING = "TASK_ID_MISSING"
    REQUESTER_MISSING = "REQUESTER_MISSING"
    AUTHORIZED_SCOPE_MISSING = "AUTHORIZED_SCOPE_MISSING"
    ACCEPTANCE_AUTHORITY_MISSING = "ACCEPTANCE_AUTHORITY_MISSING"
    ENVIRONMENT_MISSING = "ENVIRONMENT_MISSING"
    ENVIRONMENT_NOT_ALLOWED = "ENVIRONMENT_NOT_ALLOWED"
    BUDGET_MISSING = "BUDGET_MISSING"
    BUDGET_INVALID = "BUDGET_INVALID"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    REQUESTER_NOT_ALLOWED = "REQUESTER_NOT_ALLOWED"
    PATH_OUTSIDE_AUTHORIZED_SCOPE = "PATH_OUTSIDE_AUTHORIZED_SCOPE"


@dataclass(frozen=True)
class RequestBudget:
    max_attempts: int | None = None
    max_tokens: int | None = None
    max_wall_time_ms: int | None = None

    def valid(self) -> bool:
        return all(value is None or value >= 0 for value in (self.max_attempts, self.max_tokens, self.max_wall_time_ms))

    def to_dict(self) -> dict[str, int | None]:
        return {
            "max_attempts": self.max_attempts,
            "max_tokens": self.max_tokens,
            "max_wall_time_ms": self.max_wall_time_ms,
        }


@dataclass(frozen=True)
class RequestEnvironment:
    environment_id: str | None = None
    workspace: str | None = None
    revision: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "environment_id": self.environment_id,
            "workspace": self.workspace,
            "revision": self.revision,
        }


@dataclass(frozen=True)
class ArkxRequest:
    request_id: str | None
    task_id: str | None
    requester: str | None
    signals: TaskSignals
    authorized_paths: tuple[str, ...] | None
    budget: RequestBudget | None
    environment: RequestEnvironment | None
    acceptance_authority: str | None
    evidence_refs: tuple[str, ...] | None = None
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "task_id": self.task_id,
            "requester": self.requester,
            "signals": self.signals.to_dict(),
            "authorized_paths": None if self.authorized_paths is None else sorted(set(self.authorized_paths)),
            "budget": None if self.budget is None else self.budget.to_dict(),
            "environment": None if self.environment is None else self.environment.to_dict(),
            "acceptance_authority": self.acceptance_authority,
            "evidence_refs": None if self.evidence_refs is None else sorted(set(self.evidence_refs)),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class GovernancePolicy:
    authority_id: str
    allowed_requesters: tuple[str, ...] | None = None
    allowed_environments: tuple[str, ...] | None = None
    max_attempts: int | None = None
    max_tokens: int | None = None
    max_wall_time_ms: int | None = None
    require_acceptance_authority: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority_id": self.authority_id,
            "allowed_requesters": None if self.allowed_requesters is None else sorted(set(self.allowed_requesters)),
            "allowed_environments": None if self.allowed_environments is None else sorted(set(self.allowed_environments)),
            "max_attempts": self.max_attempts,
            "max_tokens": self.max_tokens,
            "max_wall_time_ms": self.max_wall_time_ms,
            "require_acceptance_authority": self.require_acceptance_authority,
        }


@dataclass(frozen=True)
class GovernanceDecision:
    request_id: str | None
    status: GovernanceStatus
    authority_id: str
    reason_codes: tuple[GovernanceReason, ...]
    request: ArkxRequest | None = None
    telemetry: dict[str, Any] = field(default_factory=dict)
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "status": self.status.value,
            "authority_id": self.authority_id,
            "reason_codes": [reason.value for reason in self.reason_codes],
            "request": None if self.request is None else self.request.to_dict(),
            "telemetry": self.telemetry,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _blocked(request: ArkxRequest, policy: GovernancePolicy, reasons: list[GovernanceReason]) -> GovernanceDecision:
    unique = tuple(dict.fromkeys(reasons))
    return GovernanceDecision(
        request_id=request.request_id,
        status=GovernanceStatus.BLOCKED,
        authority_id=policy.authority_id,
        reason_codes=unique,
        request=None,
        telemetry={"governance_status": GovernanceStatus.BLOCKED.value, "reason_codes": [reason.value for reason in unique]},
    )


def authorize_request(request: ArkxRequest, policy: GovernancePolicy) -> GovernanceDecision:
    """Authorize processing boundaries without characterizing or executing a task."""

    reasons: list[GovernanceReason] = []
    if not policy.authority_id:
        raise ValueError("governance authority_id must be explicit")
    if not request.request_id:
        reasons.append(GovernanceReason.REQUEST_ID_MISSING)
    if not request.task_id:
        reasons.append(GovernanceReason.TASK_ID_MISSING)
    if not request.requester:
        reasons.append(GovernanceReason.REQUESTER_MISSING)
    if request.authorized_paths is None or not request.authorized_paths:
        reasons.append(GovernanceReason.AUTHORIZED_SCOPE_MISSING)
    if policy.require_acceptance_authority and not request.acceptance_authority:
        reasons.append(GovernanceReason.ACCEPTANCE_AUTHORITY_MISSING)
    if request.environment is None or not request.environment.environment_id:
        reasons.append(GovernanceReason.ENVIRONMENT_MISSING)
    elif policy.allowed_environments and request.environment.environment_id not in policy.allowed_environments:
        reasons.append(GovernanceReason.ENVIRONMENT_NOT_ALLOWED)
    if request.budget is None:
        reasons.append(GovernanceReason.BUDGET_MISSING)
    elif not request.budget.valid():
        reasons.append(GovernanceReason.BUDGET_INVALID)
    else:
        limits = ((request.budget.max_attempts, policy.max_attempts), (request.budget.max_tokens, policy.max_tokens), (request.budget.max_wall_time_ms, policy.max_wall_time_ms))
        if any(value is not None and limit is not None and value > limit for value, limit in limits):
            reasons.append(GovernanceReason.BUDGET_EXCEEDED)
    if policy.allowed_requesters and request.requester not in policy.allowed_requesters:
        reasons.append(GovernanceReason.REQUESTER_NOT_ALLOWED)
    if request.authorized_paths and request.signals.candidate_files:
        prefixes = tuple(path.rstrip("/") + "/" for path in request.authorized_paths)
        if any(not any(file == path.rstrip("/") or file.startswith(path_prefix) for path, path_prefix in zip(request.authorized_paths, prefixes)) for file in request.signals.candidate_files):
            reasons.append(GovernanceReason.PATH_OUTSIDE_AUTHORIZED_SCOPE)

    if reasons:
        return _blocked(request, policy, reasons)
    return GovernanceDecision(
        request_id=request.request_id,
        status=GovernanceStatus.AUTHORIZED,
        authority_id=policy.authority_id,
        reason_codes=(GovernanceReason.AUTHORIZED,),
        request=request,
        telemetry={"governance_status": GovernanceStatus.AUTHORIZED.value, "reason_codes": [GovernanceReason.AUTHORIZED.value]},
    )


def characterize_authorized_request(
    decision: GovernanceDecision,
    *,
    config: CharacterizationConfig | None = None,
) -> TaskCharacterization | None:
    """Characterize only an authorized request; governance remains authoritative."""

    if decision.status is not GovernanceStatus.AUTHORIZED or decision.request is None:
        return None
    return characterize(decision.request.signals, config=config or CharacterizationConfig())
