"""Governed execution spine through independent verification.

This module composes existing contracts while preserving their authority
boundaries. It does not implement recovery, acceptance, promotion, or a
concrete executor adapter.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import hashlib
import json
from typing import Any, Protocol

from .characterization import TaskCharacterization, TaskSignals, characterize
from .command import CommandResult
from .governance import (
    AuthorityGrant,
    GovernanceDecision,
    GovernanceStatus,
    TaskRequest,
    evaluate_governance,
)
from .progress import ProgressAssessment, ProgressSnapshot, assess_progress
from .qualification import (
    BindingStatus,
    CapabilityRequirement,
    ExecutorBinding,
    ExecutorQualification,
    ExecutorRuntime,
    bind_executor,
)
from .routing import (
    RoutingDecision,
    RoutingDecisionType,
    route_characterization,
)
from .verification import (
    PatchVerificationInput,
    PatchVerificationResult,
    PatchVerificationStatus,
    verify_patch,
)


SCHEMA_VERSION = 1


class SpineStatus(str, Enum):
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"
    REQUIRE_QUALIFICATION = "REQUIRE_QUALIFICATION"
    INVALID = "INVALID"
    EXECUTED = "EXECUTED"
    READY_FOR_ACCEPTANCE = "READY_FOR_ACCEPTANCE"
    REJECTED = "REJECTED"


class InvocationState(str, Enum):
    NOT_EXECUTED = "NOT_EXECUTED"
    OBSERVED = "OBSERVED"


class SpineReason(str, Enum):
    GOVERNANCE_BLOCKED = "GOVERNANCE_BLOCKED"
    GOVERNANCE_UNKNOWN = "GOVERNANCE_UNKNOWN"
    CHARACTERIZATION_SCOPE_OUTSIDE_REQUEST = "CHARACTERIZATION_SCOPE_OUTSIDE_REQUEST"
    ROUTING_REQUIRES_QUALIFICATION = "ROUTING_REQUIRES_QUALIFICATION"
    ROUTING_INVALID = "ROUTING_INVALID"
    BINDING_REQUIRES_QUALIFICATION = "BINDING_REQUIRES_QUALIFICATION"
    BINDING_BLOCKED = "BINDING_BLOCKED"
    EXECUTOR_IDENTITY_MISMATCH = "EXECUTOR_IDENTITY_MISMATCH"
    ENVIRONMENT_ERROR = "ENVIRONMENT_ERROR"
    COMMAND_TIMEOUT = "COMMAND_TIMEOUT"
    EXECUTION_OBSERVED = "EXECUTION_OBSERVED"
    VERIFICATION_VERIFIED = "VERIFICATION_VERIFIED"
    VERIFICATION_REJECTED = "VERIFICATION_REJECTED"
    VERIFICATION_BLOCKED = "VERIFICATION_BLOCKED"
    VERIFICATION_UNKNOWN = "VERIFICATION_UNKNOWN"


class BoundExecutorInvoker(Protocol):
    @property
    def identity(self) -> tuple[str, str, str, str]:
        """Exact executor/version/adapter/version identity."""

    def invoke(
        self,
        *,
        request: TaskRequest,
        governance: GovernanceDecision,
        routing: RoutingDecision,
        binding: ExecutorBinding,
        timeout_seconds: float,
    ) -> CommandResult:
        """Produce one command observation for an already-bound executor."""


@dataclass(frozen=True)
class GovernedExecutionRecord:
    request_id: str
    task_ref: str
    requested_scope: tuple[str, ...]
    status: SpineStatus
    reason: SpineReason
    invocation_state: InvocationState
    acceptance_authority_ref: str | None
    governance: GovernanceDecision
    characterization: TaskCharacterization | None = None
    characterization_ref: str | None = None
    routing: RoutingDecision | None = None
    routing_ref: str | None = None
    capability_requirement: CapabilityRequirement | None = None
    binding: ExecutorBinding | None = None
    command_result: CommandResult | None = None
    progress: ProgressAssessment | None = None
    verification: PatchVerificationResult | None = None
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.request_id.strip() or not self.task_ref.strip():
            raise ValueError("request_id and task_ref must be non-empty")
        if not self.requested_scope or any(
            not isinstance(item, str) or not item.strip() for item in self.requested_scope
        ):
            raise ValueError("requested_scope must contain non-blank entries")
        if not isinstance(self.status, SpineStatus):
            raise ValueError("status must be a SpineStatus")
        if not isinstance(self.reason, SpineReason):
            raise ValueError("reason must be a SpineReason")
        if not isinstance(self.invocation_state, InvocationState):
            raise ValueError("invocation_state must be an InvocationState")
        if not isinstance(self.governance, GovernanceDecision):
            raise ValueError("governance must be a GovernanceDecision")
        if isinstance(self.schema_version, bool) or self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported governed execution schema: {self.schema_version}")

        if self.invocation_state is InvocationState.NOT_EXECUTED and self.command_result is not None:
            raise ValueError("NOT_EXECUTED cannot carry a command result")
        if self.invocation_state is InvocationState.OBSERVED and self.command_result is None:
            raise ValueError("OBSERVED requires a command result")
        if self.command_result is not None:
            if self.governance.status is not GovernanceStatus.AUTHORIZED:
                raise ValueError("command observations require authorized governance")
            if self.binding is None or self.binding.status is not BindingStatus.BOUND:
                raise ValueError("command observations require a bound executor")
            if self.routing is None or self.routing.decision is not RoutingDecisionType.ROUTE:
                raise ValueError("command observations require a valid route")

        if self.verification is not None:
            if self.command_result is None or self.progress is None:
                raise ValueError("verification requires command observation and progress assessment")
            if self.verification.task_id != self.task_ref:
                raise ValueError("verification task_id must match the governed task_ref")

        if self.status is SpineStatus.READY_FOR_ACCEPTANCE:
            if (
                self.verification is None
                or self.verification.status is not PatchVerificationStatus.VERIFIED
                or not (self.acceptance_authority_ref or "").strip()
            ):
                raise ValueError(
                    "READY_FOR_ACCEPTANCE requires VERIFIED result and acceptance authority"
                )
        if self.status is SpineStatus.REJECTED:
            if (
                self.verification is None
                or self.verification.status is not PatchVerificationStatus.REJECTED
            ):
                raise ValueError("REJECTED requires a rejected verification result")
        if self.status is SpineStatus.EXECUTED and self.invocation_state is not InvocationState.OBSERVED:
            raise ValueError("EXECUTED requires an observed invocation")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "task_ref": self.task_ref,
            "requested_scope": list(self.requested_scope),
            "status": self.status.value,
            "reason": self.reason.value,
            "invocation_state": self.invocation_state.value,
            "acceptance_authority_ref": self.acceptance_authority_ref,
            "governance": self.governance.to_dict(),
            "characterization": (
                None if self.characterization is None else self.characterization.to_dict()
            ),
            "characterization_ref": self.characterization_ref,
            "routing": None if self.routing is None else self.routing.to_dict(),
            "routing_ref": self.routing_ref,
            "capability_requirement": (
                None
                if self.capability_requirement is None
                else self.capability_requirement.to_dict()
            ),
            "binding": None if self.binding is None else self.binding.to_dict(),
            "command_result": (
                None if self.command_result is None else self.command_result.to_dict()
            ),
            "progress": None if self.progress is None else self.progress.to_dict(),
            "verification": (
                None if self.verification is None else self.verification.to_dict()
            ),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )


def execute_governed(
    request: TaskRequest,
    grant: AuthorityGrant | None,
    signals: TaskSignals,
    *,
    capability_id: str,
    runtimes: tuple[ExecutorRuntime, ...],
    qualifications: tuple[ExecutorQualification, ...],
    executor: BoundExecutorInvoker,
) -> GovernedExecutionRecord:
    """Run authority, characterization, routing, binding, then one invocation."""

    governance = evaluate_governance(request, grant)
    acceptance_authority = (
        governance.acceptance_authority_ref
        if governance.status is GovernanceStatus.AUTHORIZED
        else None
    )
    if governance.status is GovernanceStatus.BLOCKED:
        return _record(
            request,
            governance,
            SpineStatus.BLOCKED,
            SpineReason.GOVERNANCE_BLOCKED,
            acceptance_authority_ref=acceptance_authority,
        )
    if governance.status is GovernanceStatus.UNKNOWN:
        return _record(
            request,
            governance,
            SpineStatus.UNKNOWN,
            SpineReason.GOVERNANCE_UNKNOWN,
            acceptance_authority_ref=acceptance_authority,
        )

    normalized_signals = signals.normalized()
    if (
        normalized_signals.candidate_files is not None
        and any(
            not _path_within_requested_scope(path, request.requested_scope)
            for path in normalized_signals.candidate_files
        )
    ):
        return _record(
            request,
            governance,
            SpineStatus.BLOCKED,
            SpineReason.CHARACTERIZATION_SCOPE_OUTSIDE_REQUEST,
            acceptance_authority_ref=acceptance_authority,
        )

    characterization = characterize(normalized_signals)
    characterization_ref = _artifact_ref("characterization", characterization.to_json())
    routing = route_characterization(
        request.task_ref,
        characterization,
        characterization_ref=characterization_ref,
    )
    routing_ref = _artifact_ref("routing", routing.to_json())

    if routing.decision is RoutingDecisionType.REQUIRE_QUALIFICATION:
        return _record(
            request,
            governance,
            SpineStatus.REQUIRE_QUALIFICATION,
            SpineReason.ROUTING_REQUIRES_QUALIFICATION,
            acceptance_authority_ref=acceptance_authority,
            characterization=characterization,
            characterization_ref=characterization_ref,
            routing=routing,
            routing_ref=routing_ref,
        )
    if routing.decision is RoutingDecisionType.REJECT_INVALID_INPUT:
        return _record(
            request,
            governance,
            SpineStatus.INVALID,
            SpineReason.ROUTING_INVALID,
            acceptance_authority_ref=acceptance_authority,
            characterization=characterization,
            characterization_ref=characterization_ref,
            routing=routing,
            routing_ref=routing_ref,
        )

    if not isinstance(capability_id, str) or not capability_id.strip():
        raise ValueError("capability_id must be non-empty")
    requirement = CapabilityRequirement(
        requirement_id=f"{request.request_id}:capability",
        capability_id=capability_id,
        source_ref=routing_ref,
    )
    binding = bind_executor(requirement, runtimes, qualifications)

    if binding.status is BindingStatus.REQUIRE_QUALIFICATION:
        return _record(
            request,
            governance,
            SpineStatus.REQUIRE_QUALIFICATION,
            SpineReason.BINDING_REQUIRES_QUALIFICATION,
            acceptance_authority_ref=acceptance_authority,
            characterization=characterization,
            characterization_ref=characterization_ref,
            routing=routing,
            routing_ref=routing_ref,
            capability_requirement=requirement,
            binding=binding,
        )
    if binding.status is BindingStatus.BLOCKED:
        return _record(
            request,
            governance,
            SpineStatus.BLOCKED,
            SpineReason.BINDING_BLOCKED,
            acceptance_authority_ref=acceptance_authority,
            characterization=characterization,
            characterization_ref=characterization_ref,
            routing=routing,
            routing_ref=routing_ref,
            capability_requirement=requirement,
            binding=binding,
        )

    expected_identity = (
        binding.executor_id,
        binding.executor_version,
        binding.adapter_id,
        binding.adapter_version,
    )
    if executor.identity != expected_identity:
        return _record(
            request,
            governance,
            SpineStatus.BLOCKED,
            SpineReason.EXECUTOR_IDENTITY_MISMATCH,
            acceptance_authority_ref=acceptance_authority,
            characterization=characterization,
            characterization_ref=characterization_ref,
            routing=routing,
            routing_ref=routing_ref,
            capability_requirement=requirement,
            binding=binding,
        )

    assert governance.max_wall_time_seconds is not None
    result = executor.invoke(
        request=request,
        governance=governance,
        routing=routing,
        binding=binding,
        timeout_seconds=governance.max_wall_time_seconds,
    )
    common = dict(
        acceptance_authority_ref=acceptance_authority,
        characterization=characterization,
        characterization_ref=characterization_ref,
        routing=routing,
        routing_ref=routing_ref,
        capability_requirement=requirement,
        binding=binding,
        command_result=result,
        invocation_state=InvocationState.OBSERVED,
    )
    if result.timed_out:
        return _record(
            request,
            governance,
            SpineStatus.BLOCKED,
            SpineReason.COMMAND_TIMEOUT,
            **common,
        )
    if result.environment_error is not None:
        return _record(
            request,
            governance,
            SpineStatus.BLOCKED,
            SpineReason.ENVIRONMENT_ERROR,
            **common,
        )
    return _record(
        request,
        governance,
        SpineStatus.EXECUTED,
        SpineReason.EXECUTION_OBSERVED,
        **common,
    )


def verify_observation(
    record: GovernedExecutionRecord,
    previous_progress: ProgressSnapshot | None,
    current_progress: ProgressSnapshot,
    verification_input: PatchVerificationInput,
) -> GovernedExecutionRecord:
    """Assess progress and independently verify one already-observed execution."""

    if record.status is not SpineStatus.EXECUTED:
        raise ValueError("verification requires an EXECUTED spine record")
    if record.invocation_state is not InvocationState.OBSERVED or record.command_result is None:
        raise ValueError("verification requires an observed command result")
    if verification_input.task_id != record.task_ref:
        raise ValueError("verification input task_id must match record task_ref")
    if (
        verification_input.expected_scope is not None
        and not set(verification_input.expected_scope).issubset(record.requested_scope)
    ):
        raise ValueError("verification expected_scope cannot exceed requested_scope")

    progress = assess_progress(previous_progress, current_progress)
    verification = verify_patch(verification_input)
    mapping = {
        PatchVerificationStatus.VERIFIED: (
            SpineStatus.READY_FOR_ACCEPTANCE,
            SpineReason.VERIFICATION_VERIFIED,
        ),
        PatchVerificationStatus.REJECTED: (
            SpineStatus.REJECTED,
            SpineReason.VERIFICATION_REJECTED,
        ),
        PatchVerificationStatus.BLOCKED: (
            SpineStatus.BLOCKED,
            SpineReason.VERIFICATION_BLOCKED,
        ),
        PatchVerificationStatus.UNKNOWN: (
            SpineStatus.UNKNOWN,
            SpineReason.VERIFICATION_UNKNOWN,
        ),
    }
    status, reason = mapping[verification.status]
    return replace(
        record,
        status=status,
        reason=reason,
        progress=progress,
        verification=verification,
    )


def _record(
    request: TaskRequest,
    governance: GovernanceDecision,
    status: SpineStatus,
    reason: SpineReason,
    *,
    invocation_state: InvocationState = InvocationState.NOT_EXECUTED,
    acceptance_authority_ref: str | None = None,
    characterization: TaskCharacterization | None = None,
    characterization_ref: str | None = None,
    routing: RoutingDecision | None = None,
    routing_ref: str | None = None,
    capability_requirement: CapabilityRequirement | None = None,
    binding: ExecutorBinding | None = None,
    command_result: CommandResult | None = None,
) -> GovernedExecutionRecord:
    return GovernedExecutionRecord(
        request_id=request.request_id,
        task_ref=request.task_ref,
        requested_scope=request.requested_scope,
        status=status,
        reason=reason,
        invocation_state=invocation_state,
        acceptance_authority_ref=acceptance_authority_ref,
        governance=governance,
        characterization=characterization,
        characterization_ref=characterization_ref,
        routing=routing,
        routing_ref=routing_ref,
        capability_requirement=capability_requirement,
        binding=binding,
        command_result=command_result,
    )


def _path_within_requested_scope(path: str, requested_scope: tuple[str, ...]) -> bool:
    normalized = path.replace("\\", "/").strip("/")
    return any(
        normalized == allowed.replace("\\", "/").strip("/")
        or normalized.startswith(allowed.replace("\\", "/").strip("/").rstrip("/") + "/")
        for allowed in requested_scope
    )


def _artifact_ref(kind: str, payload: str) -> str:
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{kind}:sha256:{digest}"
