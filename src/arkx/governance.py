"""Request/governance contracts that authorize scope and budgets without choosing executors."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from math import isfinite
from typing import Any


SCHEMA_VERSION = 1


class GovernanceStatus(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class GovernanceReason(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    MISSING_AUTHORITY = "MISSING_AUTHORITY"
    AUTHORITY_REQUEST_MISMATCH = "AUTHORITY_REQUEST_MISMATCH"
    SCOPE_UNKNOWN = "SCOPE_UNKNOWN"
    PERMISSIONS_UNKNOWN = "PERMISSIONS_UNKNOWN"
    BUDGET_UNKNOWN = "BUDGET_UNKNOWN"
    ENVIRONMENT_UNKNOWN = "ENVIRONMENT_UNKNOWN"
    ACCEPTANCE_AUTHORITY_UNKNOWN = "ACCEPTANCE_AUTHORITY_UNKNOWN"
    SCOPE_DENIED = "SCOPE_DENIED"
    PERMISSION_DENIED = "PERMISSION_DENIED"


def _nonblank(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _optional_nonblank(name: str, value: Any) -> str | None:
    if value is None:
        return None
    return _nonblank(name, value)


def _strings(name: str, values: tuple[str, ...], *, allow_empty: bool) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ValueError(f"{name} must be a tuple")
    if not allow_empty and not values:
        raise ValueError(f"{name} must be non-empty")
    if any(not isinstance(item, str) or not item.strip() for item in values):
        raise ValueError(f"{name} must contain only non-blank strings")
    return tuple(sorted(set(values)))


def _optional_strings(name: str, values: tuple[str, ...] | None) -> tuple[str, ...] | None:
    if values is None:
        return None
    return _strings(name, values, allow_empty=True)


def _positive_int(name: str, value: int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer when present")
    return value


def _positive_number(name: str, value: float | int | None) -> float | None:
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(float(value))
        or value <= 0
    ):
        raise ValueError(f"{name} must be a finite positive number when present")
    return float(value)


def _json(value: dict[str, Any]) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


@dataclass(frozen=True)
class TaskRequest:
    request_id: str
    requester_ref: str
    task_ref: str
    project_ref: str
    requested_scope: tuple[str, ...]
    required_permissions: tuple[str, ...]
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("request_id", "requester_ref", "task_ref", "project_ref"):
            _nonblank(name, getattr(self, name))
        object.__setattr__(
            self,
            "requested_scope",
            _strings("requested_scope", self.requested_scope, allow_empty=False),
        )
        object.__setattr__(
            self,
            "required_permissions",
            _strings("required_permissions", self.required_permissions, allow_empty=True),
        )
        if isinstance(self.schema_version, bool) or self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported task request schema: {self.schema_version}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "requester_ref": self.requester_ref,
            "task_ref": self.task_ref,
            "project_ref": self.project_ref,
            "requested_scope": list(self.requested_scope),
            "required_permissions": list(self.required_permissions),
        }

    def to_json(self) -> str:
        return _json(self.to_dict())


@dataclass(frozen=True)
class AuthorityGrant:
    grant_id: str
    request_id: str
    authority_ref: str
    authorized_scope: tuple[str, ...] | None
    permissions: tuple[str, ...] | None
    max_commands: int | None
    max_wall_time_seconds: float | None
    environment_ref: str | None
    acceptance_authority_ref: str | None
    evidence_refs: tuple[str, ...]
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("grant_id", "request_id", "authority_ref"):
            _nonblank(name, getattr(self, name))
        object.__setattr__(
            self,
            "authorized_scope",
            _optional_strings("authorized_scope", self.authorized_scope),
        )
        object.__setattr__(
            self,
            "permissions",
            _optional_strings("permissions", self.permissions),
        )
        object.__setattr__(self, "max_commands", _positive_int("max_commands", self.max_commands))
        object.__setattr__(
            self,
            "max_wall_time_seconds",
            _positive_number("max_wall_time_seconds", self.max_wall_time_seconds),
        )
        object.__setattr__(
            self,
            "environment_ref",
            _optional_nonblank("environment_ref", self.environment_ref),
        )
        object.__setattr__(
            self,
            "acceptance_authority_ref",
            _optional_nonblank("acceptance_authority_ref", self.acceptance_authority_ref),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            _strings("evidence_refs", self.evidence_refs, allow_empty=False),
        )
        if isinstance(self.schema_version, bool) or self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported authority grant schema: {self.schema_version}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "grant_id": self.grant_id,
            "request_id": self.request_id,
            "authority_ref": self.authority_ref,
            "authorized_scope": (
                None if self.authorized_scope is None else list(self.authorized_scope)
            ),
            "permissions": None if self.permissions is None else list(self.permissions),
            "max_commands": self.max_commands,
            "max_wall_time_seconds": self.max_wall_time_seconds,
            "environment_ref": self.environment_ref,
            "acceptance_authority_ref": self.acceptance_authority_ref,
            "evidence_refs": list(self.evidence_refs),
        }

    def to_json(self) -> str:
        return _json(self.to_dict())


@dataclass(frozen=True)
class GovernanceDecision:
    request_id: str
    status: GovernanceStatus
    reasons: tuple[GovernanceReason, ...]
    grant_id: str | None = None
    authority_ref: str | None = None
    authorized_scope: tuple[str, ...] | None = None
    permissions: tuple[str, ...] | None = None
    max_commands: int | None = None
    max_wall_time_seconds: float | None = None
    environment_ref: str | None = None
    acceptance_authority_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _nonblank("request_id", self.request_id)
        if not isinstance(self.status, GovernanceStatus):
            raise ValueError("status must be a GovernanceStatus")
        if not isinstance(self.reasons, tuple) or not self.reasons:
            raise ValueError("reasons must be a non-empty tuple")
        if any(not isinstance(reason, GovernanceReason) for reason in self.reasons):
            raise ValueError("reasons must contain GovernanceReason values")
        object.__setattr__(
            self,
            "reasons",
            tuple(sorted(set(self.reasons), key=lambda item: item.value)),
        )
        object.__setattr__(self, "grant_id", _optional_nonblank("grant_id", self.grant_id))
        object.__setattr__(
            self,
            "authority_ref",
            _optional_nonblank("authority_ref", self.authority_ref),
        )
        object.__setattr__(
            self,
            "authorized_scope",
            _optional_strings("authorized_scope", self.authorized_scope),
        )
        object.__setattr__(
            self,
            "permissions",
            _optional_strings("permissions", self.permissions),
        )
        if self.evidence_refs:
            object.__setattr__(
                self,
                "evidence_refs",
                _strings("evidence_refs", self.evidence_refs, allow_empty=False),
            )

        if self.status is GovernanceStatus.AUTHORIZED:
            required_strings = {
                "grant_id": self.grant_id,
                "authority_ref": self.authority_ref,
                "environment_ref": self.environment_ref,
                "acceptance_authority_ref": self.acceptance_authority_ref,
            }
            for name, value in required_strings.items():
                _nonblank(name, value)
            if self.authorized_scope is None or not self.authorized_scope:
                raise ValueError("AUTHORIZED requires non-empty authorized_scope")
            if self.permissions is None:
                raise ValueError("AUTHORIZED requires explicit permissions")
            if self.max_commands is None or self.max_wall_time_seconds is None:
                raise ValueError("AUTHORIZED requires explicit execution budgets")
            _positive_int("max_commands", self.max_commands)
            _positive_number("max_wall_time_seconds", self.max_wall_time_seconds)
            if not self.evidence_refs:
                raise ValueError("AUTHORIZED requires evidence_refs")
            if self.reasons != (GovernanceReason.AUTHORIZED,):
                raise ValueError("AUTHORIZED requires the AUTHORIZED reason only")
        else:
            operational = (
                self.authorized_scope,
                self.permissions,
                self.max_commands,
                self.max_wall_time_seconds,
                self.environment_ref,
                self.acceptance_authority_ref,
            )
            if any(value is not None for value in operational):
                raise ValueError("non-authorized decisions cannot carry executable authority")

        if isinstance(self.schema_version, bool) or self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported governance decision schema: {self.schema_version}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "status": self.status.value,
            "reasons": [reason.value for reason in self.reasons],
            "grant_id": self.grant_id,
            "authority_ref": self.authority_ref,
            "authorized_scope": (
                None if self.authorized_scope is None else list(self.authorized_scope)
            ),
            "permissions": None if self.permissions is None else list(self.permissions),
            "max_commands": self.max_commands,
            "max_wall_time_seconds": self.max_wall_time_seconds,
            "environment_ref": self.environment_ref,
            "acceptance_authority_ref": self.acceptance_authority_ref,
            "evidence_refs": list(self.evidence_refs),
        }

    def to_json(self) -> str:
        return _json(self.to_dict())


def evaluate_governance(
    request: TaskRequest,
    grant: AuthorityGrant | None,
) -> GovernanceDecision:
    if grant is None:
        return _decision(
            request,
            GovernanceStatus.BLOCKED,
            (GovernanceReason.MISSING_AUTHORITY,),
        )

    if grant.request_id != request.request_id:
        return _decision(
            request,
            GovernanceStatus.BLOCKED,
            (GovernanceReason.AUTHORITY_REQUEST_MISMATCH,),
            grant=grant,
        )

    unknown: list[GovernanceReason] = []
    if grant.authorized_scope is None:
        unknown.append(GovernanceReason.SCOPE_UNKNOWN)
    if grant.permissions is None:
        unknown.append(GovernanceReason.PERMISSIONS_UNKNOWN)
    if grant.max_commands is None or grant.max_wall_time_seconds is None:
        unknown.append(GovernanceReason.BUDGET_UNKNOWN)
    if grant.environment_ref is None:
        unknown.append(GovernanceReason.ENVIRONMENT_UNKNOWN)
    if grant.acceptance_authority_ref is None:
        unknown.append(GovernanceReason.ACCEPTANCE_AUTHORITY_UNKNOWN)
    if unknown:
        return _decision(
            request,
            GovernanceStatus.UNKNOWN,
            tuple(unknown),
            grant=grant,
        )

    assert grant.authorized_scope is not None
    assert grant.permissions is not None
    if not set(request.requested_scope).issubset(grant.authorized_scope):
        return _decision(
            request,
            GovernanceStatus.BLOCKED,
            (GovernanceReason.SCOPE_DENIED,),
            grant=grant,
        )
    if not set(request.required_permissions).issubset(grant.permissions):
        return _decision(
            request,
            GovernanceStatus.BLOCKED,
            (GovernanceReason.PERMISSION_DENIED,),
            grant=grant,
        )

    return GovernanceDecision(
        request_id=request.request_id,
        status=GovernanceStatus.AUTHORIZED,
        reasons=(GovernanceReason.AUTHORIZED,),
        grant_id=grant.grant_id,
        authority_ref=grant.authority_ref,
        authorized_scope=grant.authorized_scope,
        permissions=grant.permissions,
        max_commands=grant.max_commands,
        max_wall_time_seconds=grant.max_wall_time_seconds,
        environment_ref=grant.environment_ref,
        acceptance_authority_ref=grant.acceptance_authority_ref,
        evidence_refs=grant.evidence_refs,
    )


def _decision(
    request: TaskRequest,
    status: GovernanceStatus,
    reasons: tuple[GovernanceReason, ...],
    *,
    grant: AuthorityGrant | None = None,
) -> GovernanceDecision:
    return GovernanceDecision(
        request_id=request.request_id,
        status=status,
        reasons=reasons,
        grant_id=None if grant is None else grant.grant_id,
        authority_ref=None if grant is None else grant.authority_ref,
        evidence_refs=() if grant is None else grant.evidence_refs,
    )
