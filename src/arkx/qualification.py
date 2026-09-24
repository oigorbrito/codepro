"""Capability qualification and executor binding without hidden ranking."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Any


SCHEMA_VERSION = 1


class QualificationStatus(str, Enum):
    QUALIFIED = "QUALIFIED"
    NOT_QUALIFIED = "NOT_QUALIFIED"


class BindingStatus(str, Enum):
    BOUND = "BOUND"
    REQUIRE_QUALIFICATION = "REQUIRE_QUALIFICATION"
    BLOCKED = "BLOCKED"


class BindingReason(str, Enum):
    SINGLE_QUALIFIED_EXECUTOR = "SINGLE_QUALIFIED_EXECUTOR"
    NO_EXECUTOR_AVAILABLE = "NO_EXECUTOR_AVAILABLE"
    QUALIFIED_EXECUTOR_UNAVAILABLE = "QUALIFIED_EXECUTOR_UNAVAILABLE"
    NO_QUALIFICATION_FOR_AVAILABLE_EXECUTOR = "NO_QUALIFICATION_FOR_AVAILABLE_EXECUTOR"
    AVAILABLE_IDENTITY_NOT_QUALIFIED = "AVAILABLE_IDENTITY_NOT_QUALIFIED"
    AMBIGUOUS_QUALIFIED_EXECUTORS = "AMBIGUOUS_QUALIFIED_EXECUTORS"


def _nonblank(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _refs(name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(values, tuple) or not values:
        raise ValueError(f"{name} must be a non-empty tuple")
    if any(not isinstance(item, str) or not item.strip() for item in values):
        raise ValueError(f"{name} must contain only non-blank strings")
    return tuple(sorted(set(values)))


def _json(value: dict[str, Any]) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


@dataclass(frozen=True)
class CapabilityRequirement:
    requirement_id: str
    capability_id: str
    source_ref: str
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _nonblank("requirement_id", self.requirement_id)
        _nonblank("capability_id", self.capability_id)
        _nonblank("source_ref", self.source_ref)
        if isinstance(self.schema_version, bool) or self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported capability requirement schema: {self.schema_version}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "requirement_id": self.requirement_id,
            "capability_id": self.capability_id,
            "source_ref": self.source_ref,
        }


@dataclass(frozen=True)
class ExecutorRuntime:
    executor_id: str
    executor_version: str
    adapter_id: str
    adapter_version: str
    available: bool
    evidence_ref: str
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("executor_id", "executor_version", "adapter_id", "adapter_version", "evidence_ref"):
            _nonblank(name, getattr(self, name))
        if not isinstance(self.available, bool):
            raise ValueError("available must be boolean")
        if isinstance(self.schema_version, bool) or self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported executor runtime schema: {self.schema_version}")

    @property
    def identity(self) -> tuple[str, str, str, str]:
        return (
            self.executor_id,
            self.executor_version,
            self.adapter_id,
            self.adapter_version,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "executor_id": self.executor_id,
            "executor_version": self.executor_version,
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "available": self.available,
            "evidence_ref": self.evidence_ref,
        }


@dataclass(frozen=True)
class ExecutorQualification:
    executor_id: str
    executor_version: str
    adapter_id: str
    adapter_version: str
    capability_id: str
    status: QualificationStatus
    evidence_refs: tuple[str, ...]
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "executor_id",
            "executor_version",
            "adapter_id",
            "adapter_version",
            "capability_id",
        ):
            _nonblank(name, getattr(self, name))
        if not isinstance(self.status, QualificationStatus):
            raise ValueError("status must be a QualificationStatus")
        object.__setattr__(self, "evidence_refs", _refs("evidence_refs", self.evidence_refs))
        if isinstance(self.schema_version, bool) or self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported executor qualification schema: {self.schema_version}")

    @property
    def identity(self) -> tuple[str, str, str, str]:
        return (
            self.executor_id,
            self.executor_version,
            self.adapter_id,
            self.adapter_version,
        )

    @property
    def key(self) -> tuple[str, str, str, str, str]:
        return (*self.identity, self.capability_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "executor_id": self.executor_id,
            "executor_version": self.executor_version,
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "capability_id": self.capability_id,
            "status": self.status.value,
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class ExecutorBinding:
    requirement_id: str
    capability_id: str
    status: BindingStatus
    reason: BindingReason
    executor_id: str | None = None
    executor_version: str | None = None
    adapter_id: str | None = None
    adapter_version: str | None = None
    availability_evidence_ref: str | None = None
    qualification_evidence_refs: tuple[str, ...] = ()
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _nonblank("requirement_id", self.requirement_id)
        _nonblank("capability_id", self.capability_id)
        if not isinstance(self.status, BindingStatus):
            raise ValueError("status must be a BindingStatus")
        if not isinstance(self.reason, BindingReason):
            raise ValueError("reason must be a BindingReason")
        bound_fields = (
            self.executor_id,
            self.executor_version,
            self.adapter_id,
            self.adapter_version,
            self.availability_evidence_ref,
        )
        if self.status is BindingStatus.BOUND:
            if any(value is None or not value.strip() for value in bound_fields):
                raise ValueError("BOUND requires complete executor and availability identity")
            object.__setattr__(
                self,
                "qualification_evidence_refs",
                _refs("qualification_evidence_refs", self.qualification_evidence_refs),
            )
        elif any(value is not None for value in bound_fields) or self.qualification_evidence_refs:
            raise ValueError("non-BOUND results cannot carry an executor binding")
        if isinstance(self.schema_version, bool) or self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported executor binding schema: {self.schema_version}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "requirement_id": self.requirement_id,
            "capability_id": self.capability_id,
            "status": self.status.value,
            "reason": self.reason.value,
            "executor_id": self.executor_id,
            "executor_version": self.executor_version,
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "availability_evidence_ref": self.availability_evidence_ref,
            "qualification_evidence_refs": list(self.qualification_evidence_refs),
        }

    def to_json(self) -> str:
        return _json(self.to_dict())


def bind_executor(
    requirement: CapabilityRequirement,
    runtimes: tuple[ExecutorRuntime, ...],
    qualifications: tuple[ExecutorQualification, ...],
) -> ExecutorBinding:
    _validate_unique(runtimes, qualifications)

    relevant_qualifications = tuple(
        item for item in qualifications if item.capability_id == requirement.capability_id
    )
    qualified = tuple(
        item
        for item in relevant_qualifications
        if item.status is QualificationStatus.QUALIFIED
    )
    available = tuple(item for item in runtimes if item.available)

    if not available:
        return _unbound(
            requirement,
            BindingStatus.BLOCKED,
            (
                BindingReason.QUALIFIED_EXECUTOR_UNAVAILABLE
                if qualified
                else BindingReason.NO_EXECUTOR_AVAILABLE
            ),
        )

    qualified_by_identity = {
        item.identity: item
        for item in qualified
    }
    candidates = tuple(
        (runtime, qualified_by_identity[runtime.identity])
        for runtime in available
        if runtime.identity in qualified_by_identity
    )

    if len(candidates) > 1:
        return _unbound(
            requirement,
            BindingStatus.BLOCKED,
            BindingReason.AMBIGUOUS_QUALIFIED_EXECUTORS,
        )

    if len(candidates) == 1:
        runtime, qualification = candidates[0]
        return ExecutorBinding(
            requirement_id=requirement.requirement_id,
            capability_id=requirement.capability_id,
            status=BindingStatus.BOUND,
            reason=BindingReason.SINGLE_QUALIFIED_EXECUTOR,
            executor_id=runtime.executor_id,
            executor_version=runtime.executor_version,
            adapter_id=runtime.adapter_id,
            adapter_version=runtime.adapter_version,
            availability_evidence_ref=runtime.evidence_ref,
            qualification_evidence_refs=qualification.evidence_refs,
        )

    exact_nonqualified = {
        item.identity
        for item in relevant_qualifications
        if item.status is QualificationStatus.NOT_QUALIFIED
    }
    reason = (
        BindingReason.AVAILABLE_IDENTITY_NOT_QUALIFIED
        if any(runtime.identity in exact_nonqualified for runtime in available)
        else BindingReason.NO_QUALIFICATION_FOR_AVAILABLE_EXECUTOR
    )
    return _unbound(requirement, BindingStatus.REQUIRE_QUALIFICATION, reason)


def _unbound(
    requirement: CapabilityRequirement,
    status: BindingStatus,
    reason: BindingReason,
) -> ExecutorBinding:
    return ExecutorBinding(
        requirement_id=requirement.requirement_id,
        capability_id=requirement.capability_id,
        status=status,
        reason=reason,
    )


def _validate_unique(
    runtimes: tuple[ExecutorRuntime, ...],
    qualifications: tuple[ExecutorQualification, ...],
) -> None:
    runtime_ids = [item.identity for item in runtimes]
    if len(set(runtime_ids)) != len(runtime_ids):
        raise ValueError("executor runtime identities must be unique")

    qualification_ids = [item.key for item in qualifications]
    if len(set(qualification_ids)) != len(qualification_ids):
        raise ValueError("executor qualification identities must be unique")
