"""Sequential routed-composition orchestration contracts for P8.4.

The orchestrator wires already-qualified boundaries together. It does not
choose an executor, reinterpret verification, or cascade to another executor.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
import json
import hashlib
from typing import Any, Protocol

from .characterization import TaskCharacterization
from .outcomes import AcceptanceDecision, AcceptanceResult, VerificationResult, VerificationState
from .progress import ProgressAssessment, ProgressStatus
from .request import GovernanceDecision, GovernanceStatus
from .routing import RoutingDecision, RoutingDecisionType
from .selection import SelectionDecision, SelectionStatus
from .execution import BudgetLedger, ExecutionBudgetSpec, ExecutionPlan, ExecutionRequest, ExecutionResult as ContractExecutionResult, Executor, execution_reference
from .integration import AdapterIdentity, AdapterPreflight, IntegrationKind, PreflightStatus
from .contracts import EventType
from .harness import RunState


SCHEMA_VERSION = 1


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class ExecutionOutcome(_ValueEnum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    NOT_EXECUTED = "NOT_EXECUTED"


class OrchestrationStatus(_ValueEnum):
    BLOCKED = "BLOCKED"
    NOT_EXECUTED = "NOT_EXECUTED"
    EXECUTED = "EXECUTED"
    VERIFIED = "VERIFIED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    INDETERMINATE = "INDETERMINATE"


class OrchestrationReason(_ValueEnum):
    GOVERNANCE_REQUIRED = "GOVERNANCE_REQUIRED"
    CHARACTERIZATION_REQUIRED = "CHARACTERIZATION_REQUIRED"
    ROUTING_REQUIRED = "ROUTING_REQUIRED"
    SELECTION_REQUIRED = "SELECTION_REQUIRED"
    ACCEPTANCE_AUTHORITY_MISMATCH = "ACCEPTANCE_AUTHORITY_MISMATCH"
    EXECUTOR_FAILED = "EXECUTOR_FAILED"
    EXECUTOR_BLOCKED = "EXECUTOR_BLOCKED"
    EXECUTOR_NOT_EXECUTED = "EXECUTOR_NOT_EXECUTED"
    NO_PROGRESS = "NO_PROGRESS"
    PROGRESS_UNKNOWN = "PROGRESS_UNKNOWN"
    VERIFICATION_BLOCKED = "VERIFICATION_BLOCKED"
    VERIFICATION_UNKNOWN = "VERIFICATION_UNKNOWN"
    ACCEPTANCE_DECISION = "ACCEPTANCE_DECISION"
    CAPABILITY_PREFLIGHT_REQUIRED = "CAPABILITY_PREFLIGHT_REQUIRED"
    CAPABILITY_POLICY_BLOCKED = "CAPABILITY_POLICY_BLOCKED"
    CAPABILITY_PREFLIGHT_IDENTITY_MISMATCH = "CAPABILITY_PREFLIGHT_IDENTITY_MISMATCH"
    CAPABILITY_PREFLIGHT_PERSISTENCE_REQUIRED = "CAPABILITY_PREFLIGHT_PERSISTENCE_REQUIRED"
    LIFECYCLE_PERSISTENCE_FAILED = "LIFECYCLE_PERSISTENCE_FAILED"
    EXECUTION_BUDGET_EXHAUSTED = "EXECUTION_BUDGET_EXHAUSTED"
    BUDGET_USAGE_UNAVAILABLE = "BUDGET_USAGE_UNAVAILABLE"
    PROVIDER_PREFLIGHT_REQUIRED = "PROVIDER_PREFLIGHT_REQUIRED"
    SANDBOX_PREFLIGHT_REQUIRED = "SANDBOX_PREFLIGHT_REQUIRED"
    PROVIDER_PREFLIGHT_IDENTITY_MISMATCH = "PROVIDER_PREFLIGHT_IDENTITY_MISMATCH"
    SANDBOX_PREFLIGHT_IDENTITY_MISMATCH = "SANDBOX_PREFLIGHT_IDENTITY_MISMATCH"
    INTEGRATION_PREFLIGHT_BLOCKED = "INTEGRATION_PREFLIGHT_BLOCKED"
    INTEGRATION_PREFLIGHT_PERSISTENCE_REQUIRED = "INTEGRATION_PREFLIGHT_PERSISTENCE_REQUIRED"
    BUDGET_ENFORCEMENT_REQUIRED = "BUDGET_ENFORCEMENT_REQUIRED"


def orchestration_status_for_execution(outcome: ExecutionOutcome) -> OrchestrationStatus:
    """Map execution outcome into the orchestration result vocabulary."""
    return {
        ExecutionOutcome.COMPLETED: OrchestrationStatus.EXECUTED,
        ExecutionOutcome.FAILED: OrchestrationStatus.BLOCKED,
        ExecutionOutcome.BLOCKED: OrchestrationStatus.BLOCKED,
        ExecutionOutcome.NOT_EXECUTED: OrchestrationStatus.NOT_EXECUTED,
    }[outcome]


def orchestration_status_for_acceptance(decision: AcceptanceDecision) -> OrchestrationStatus:
    """Map acceptance decision into the orchestration result vocabulary."""
    return {
        AcceptanceDecision.ACCEPTED: OrchestrationStatus.ACCEPTED,
        AcceptanceDecision.REJECTED: OrchestrationStatus.REJECTED,
        AcceptanceDecision.BLOCKED: OrchestrationStatus.BLOCKED,
        AcceptanceDecision.NOT_EXECUTED: OrchestrationStatus.NOT_EXECUTED,
        AcceptanceDecision.INDETERMINATE: OrchestrationStatus.INDETERMINATE,
    }[decision]


@dataclass(frozen=True)
class ExecutionResult:
    run_id: str
    outcome: ExecutionOutcome
    evidence_refs: tuple[str, ...] = ()
    error: str | None = None
    telemetry: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "outcome": self.outcome.value,
            "evidence_refs": sorted(set(self.evidence_refs)),
            "error": self.error,
            "telemetry": self.telemetry,
        }


def legacy_execution_from_contract(result: "ContractExecutionResult") -> ExecutionResult:
    outcome = {
        RunState.COMPLETED: ExecutionOutcome.COMPLETED,
        RunState.FAILED: ExecutionOutcome.FAILED,
        RunState.BLOCKED: ExecutionOutcome.BLOCKED,
        RunState.UNKNOWN: ExecutionOutcome.NOT_EXECUTED,
    }.get(result.state, ExecutionOutcome.NOT_EXECUTED)
    return ExecutionResult(
        result.artifact_refs[0] if result.artifact_refs else "contract-run",
        outcome,
        result.artifact_refs,
        None if result.error is None else result.error.message,
        dict(result.usage or {}),
    )


class ExecutorRunner(Protocol):
    def run(self, request: GovernanceDecision, selection: SelectionDecision) -> ExecutionResult: ...


class BudgetEnforcedExecutorRunner(Protocol):
    """Legacy seam capability required before a budgeted execution."""

    def run_with_budget(
        self,
        request: GovernanceDecision,
        selection: SelectionDecision,
        *,
        attempt_id: str,
        budget_ledger: BudgetLedger,
    ) -> ExecutionResult: ...


class ContractExecutorRunner:
    """Bridge the neutral Executor contract into the legacy orchestration seam."""

    def __init__(self, executor: Executor) -> None:
        self.executor = executor

    def run(self, request: GovernanceDecision, selection: SelectionDecision) -> ExecutionResult:
        arkx_request = request.request
        if arkx_request is None or selection.executor is None:
            return ExecutionResult("unbound", ExecutionOutcome.NOT_EXECUTED, error="missing request or selected executor")
        environment = arkx_request.environment
        budget = arkx_request.budget
        execution_request = ExecutionRequest(
            task_id=arkx_request.task_id or "",
            task_revision=None if environment is None else environment.revision,
            treatment=selection.treatment.name if selection.treatment is not None else "",
            prompt=f"task:{arkx_request.task_id}",
            executor_id=selection.executor.executor.name,
            provider_id=None,
            model_id=None,
            sandbox_id=None if environment is None else environment.environment_id,
            budget_digest=None if budget is None else json.dumps(budget.to_dict(), sort_keys=True, separators=(",", ":")),
            configuration_digest=selection.executor.executor.configuration_digest,
        )
        return legacy_execution_from_contract(self.executor.execute(execution_request))

    def run_with_budget(
        self,
        request: GovernanceDecision,
        selection: SelectionDecision,
        *,
        attempt_id: str,
        budget_ledger: BudgetLedger,
    ) -> ExecutionResult:
        """Run only after orchestration has reserved this attempt in the ledger."""
        if attempt_id not in budget_ledger.consumed_attempts:
            return ExecutionResult("unbound", ExecutionOutcome.BLOCKED, error="budget attempt was not reserved")
        result = self.run(request, selection)
        telemetry = dict(result.telemetry)
        telemetry["budget_enforcement"] = "RESERVED_AND_MEASURED"
        return replace(result, telemetry=telemetry)


class ProgressObserver(Protocol):
    def assess(self, execution: ExecutionResult) -> ProgressAssessment: ...


class Verifier(Protocol):
    def verify(self, execution: ExecutionResult) -> VerificationResult: ...


class AcceptanceAuthority(Protocol):
    identity: str

    def decide(self, verification: VerificationResult) -> AcceptanceResult: ...


@dataclass(frozen=True)
class OrchestrationResult:
    status: OrchestrationStatus
    reason_codes: tuple[OrchestrationReason, ...]
    run_id: str | None
    execution: ExecutionResult | None = None
    plan: ExecutionPlan | None = None
    progress: ProgressAssessment | None = None
    verification: VerificationResult | None = None
    acceptance: AcceptanceResult | None = None
    telemetry: dict[str, Any] = field(default_factory=dict)
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status.value,
            "reason_codes": [reason.value for reason in self.reason_codes],
            "run_id": self.run_id,
            "execution": None if self.execution is None else self.execution.to_dict(),
            "plan": None if self.plan is None else self.plan.to_dict(),
            "progress": None if self.progress is None else self.progress.to_dict(),
            "verification": None if self.verification is None else self.verification.to_dict(),
            "acceptance": None if self.acceptance is None else self.acceptance.to_dict(),
            "telemetry": self.telemetry,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _blocked(reason: OrchestrationReason, *, run_id: str | None = None) -> OrchestrationResult:
    return OrchestrationResult(OrchestrationStatus.BLOCKED, (reason,), run_id, telemetry={"orchestration_status": OrchestrationStatus.BLOCKED.value})


def build_execution_plan(
    governance: GovernanceDecision,
    routing: RoutingDecision,
    selection: SelectionDecision,
    *,
    provider_identity: AdapterIdentity | None = None,
    sandbox_identity: AdapterIdentity | None = None,
) -> ExecutionPlan:
    request = governance.request
    if request is None or selection.executor is None or selection.treatment is None:
        raise ValueError("governance request, treatment and executor are required for an execution plan")
    identity = selection.executor.executor
    budget = None if request.budget is None else ExecutionBudgetSpec(
        max_attempts=request.budget.max_attempts,
        max_tokens=request.budget.max_tokens,
        max_wall_time_ms=request.budget.max_wall_time_ms,
    )
    payload = json.dumps({
        "request_id": request.request_id,
        "task_id": request.task_id,
        "path": routing.selected_path.value if routing.selected_path else None,
        "treatment": selection.treatment.name,
        "executor": identity.to_dict(),
        "provider": None if provider_identity is None else provider_identity.to_dict(),
        "sandbox": None if sandbox_identity is None else sandbox_identity.to_dict(),
        "budget": None if request.budget is None else request.budget.to_dict(),
    }, sort_keys=True, separators=(",", ":"))
    return ExecutionPlan(
        plan_id=hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16],
        task_id=request.task_id or "",
        task_revision=None if request.environment is None else request.environment.revision,
        treatment=selection.treatment.name,
        executor_id=identity.name,
        provider_id=None if provider_identity is None else provider_identity.name,
        model_id=None,
        sandbox_id=sandbox_identity.name if sandbox_identity is not None else (None if request.environment is None else request.environment.environment_id),
        budget_digest=None if budget is None else budget.digest(),
        configuration_digest=identity.configuration_digest,
        steps=("execute",),
        budget=budget,
        required_capabilities=selection.treatment.required_capabilities,
        provider_identity=provider_identity,
        sandbox_identity=sandbox_identity,
    )


def run_routed_pipeline(
    governance: GovernanceDecision,
    characterization: TaskCharacterization | None,
    routing: RoutingDecision | None,
    selection: SelectionDecision | None,
    executor: ExecutorRunner | Executor,
    progress_observer: ProgressObserver,
    verifier: Verifier,
    acceptance_authority: AcceptanceAuthority,
    capability_preflight: AdapterPreflight | None = None,
    event_log: Any | None = None,
    provider_identity: AdapterIdentity | None = None,
    sandbox_identity: AdapterIdentity | None = None,
    provider_preflight: AdapterPreflight | None = None,
    sandbox_preflight: AdapterPreflight | None = None,
) -> OrchestrationResult:
    """Run one selected treatment sequentially through independent gates."""

    def terminal(result: OrchestrationResult) -> OrchestrationResult:
        if event_log is None or result.run_id is None:
            return result
        try:
            event_log.append_terminal(
                timestamp=datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                status=result.status.value,
                error_code=None if not result.reason_codes else result.reason_codes[0].value,
            )
            return result
        except Exception:
            return replace(result, status=OrchestrationStatus.BLOCKED, reason_codes=(OrchestrationReason.LIFECYCLE_PERSISTENCE_FAILED,))

    if governance.status is not GovernanceStatus.AUTHORIZED or governance.request is None:
        return _blocked(OrchestrationReason.GOVERNANCE_REQUIRED)
    if characterization is None:
        return _blocked(OrchestrationReason.CHARACTERIZATION_REQUIRED)
    if routing is None or routing.decision is not RoutingDecisionType.ROUTE or routing.selected_path is None:
        return _blocked(OrchestrationReason.ROUTING_REQUIRED)
    if selection is None or selection.status is not SelectionStatus.SELECTED or selection.executor is None:
        return _blocked(OrchestrationReason.SELECTION_REQUIRED)
    if acceptance_authority.identity != governance.request.acceptance_authority:
        return _blocked(OrchestrationReason.ACCEPTANCE_AUTHORITY_MISMATCH)

    if hasattr(executor, "execute") and not hasattr(executor, "run"):
        executor = ContractExecutorRunner(executor)
    plan = build_execution_plan(governance, routing, selection, provider_identity=provider_identity, sandbox_identity=sandbox_identity)
    if plan.budget is not None and not hasattr(executor, "run_with_budget"):
        return _blocked(OrchestrationReason.BUDGET_ENFORCEMENT_REQUIRED)
    def persist_stage(stage: str, ref: str, data: dict[str, Any] | None = None) -> bool:
        if event_log is None:
            return True
        try:
            event_log.append_stage(
                timestamp=datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                event_type=EventType.EVIDENCE_ADDED,
                stage=stage,
                ref=ref,
                data=data,
            )
            return True
        except Exception:
            return False

    if not persist_stage("plan", plan.reference):
        return _blocked(OrchestrationReason.LIFECYCLE_PERSISTENCE_FAILED)
    if plan.required_capabilities:
        if capability_preflight is None:
            return _blocked(OrchestrationReason.CAPABILITY_PREFLIGHT_REQUIRED)
        if not plan.preflight_matches_identity(capability_preflight):
            return _blocked(OrchestrationReason.CAPABILITY_PREFLIGHT_IDENTITY_MISMATCH)
        capability_decision = plan.validate_capabilities(capability_preflight)
        if not capability_decision.allowed:
            return _blocked(OrchestrationReason.CAPABILITY_POLICY_BLOCKED)
        if event_log is None:
            return _blocked(OrchestrationReason.CAPABILITY_PREFLIGHT_PERSISTENCE_REQUIRED)
        if not persist_stage("preflight", capability_preflight.reference, {
            "plan_ref": plan.reference,
            "capability_digest": capability_preflight.capability_digest,
            "capability_provenance": capability_preflight.capability_provenance.value,
            "preflight_status": capability_preflight.status.value,
        }):
            return _blocked(OrchestrationReason.CAPABILITY_PREFLIGHT_PERSISTENCE_REQUIRED)
    for kind, identity, preflight, required_reason, mismatch_reason in (
        (IntegrationKind.PROVIDER, plan.provider_identity, provider_preflight, OrchestrationReason.PROVIDER_PREFLIGHT_REQUIRED, OrchestrationReason.PROVIDER_PREFLIGHT_IDENTITY_MISMATCH),
        (IntegrationKind.SANDBOX, plan.sandbox_identity, sandbox_preflight, OrchestrationReason.SANDBOX_PREFLIGHT_REQUIRED, OrchestrationReason.SANDBOX_PREFLIGHT_IDENTITY_MISMATCH),
    ):
        if identity is None:
            continue
        if preflight is None:
            return _blocked(required_reason)
        if not plan.preflight_matches_integration(preflight, kind):
            return _blocked(mismatch_reason)
        if preflight.status is not PreflightStatus.READY:
            return _blocked(OrchestrationReason.INTEGRATION_PREFLIGHT_BLOCKED)
        if event_log is None:
            return _blocked(OrchestrationReason.INTEGRATION_PREFLIGHT_PERSISTENCE_REQUIRED)
        stage = "provider_preflight" if kind is IntegrationKind.PROVIDER else "sandbox_preflight"
        if not persist_stage(stage, preflight.reference, {"integration_kind": kind.value, "preflight_status": preflight.status.value}):
            return _blocked(OrchestrationReason.INTEGRATION_PREFLIGHT_PERSISTENCE_REQUIRED)
    budget_ledger = None if plan.budget is None else BudgetLedger(plan.budget)
    if budget_ledger is not None:
        consumption = budget_ledger.consume(plan.reference, executor_invocations=1)
        if not consumption.accepted:
            return _blocked(OrchestrationReason.EXECUTION_BUDGET_EXHAUSTED)
        budget_ledger = consumption.ledger
    if plan.budget is not None:
        execution = executor.run_with_budget(governance, selection, attempt_id=plan.reference, budget_ledger=budget_ledger)
    else:
        execution = executor.run(governance, selection)
    execution_ref = execution_reference(execution.run_id)
    execution_data = {"artifact_refs": list(execution.evidence_refs), "execution_outcome": execution.outcome.value}
    if budget_ledger is not None:
        usage = execution.telemetry
        required_usage = {}
        if plan.budget.max_tokens is not None:
            required_usage["tokens"] = usage.get("total_tokens", usage.get("tokens"))
        if plan.budget.max_wall_time_ms is not None:
            required_usage["wall_time_ms"] = usage.get("wall_time_ms")
        if plan.budget.max_cost is not None:
            required_usage["cost"] = usage.get("cost")
        missing_usage = tuple(name for name, value in required_usage.items() if value is None)
        if missing_usage:
            execution_data["budget_usage_status"] = "UNAVAILABLE"
            execution_data["budget_usage_missing"] = list(missing_usage)
            budget_error = OrchestrationReason.BUDGET_USAGE_UNAVAILABLE
        else:
            measured = budget_ledger.record_usage(plan.reference, tokens=int(required_usage.get("tokens", 0)), wall_time_ms=int(required_usage.get("wall_time_ms", 0)), cost=required_usage.get("cost", 0))
            budget_ledger = measured.ledger
            budget_error = None if measured.accepted else OrchestrationReason.EXECUTION_BUDGET_EXHAUSTED
            execution_data["budget_usage_status"] = "RECORDED" if measured.accepted else "EXCEEDED"
        execution_data["budget_ledger"] = budget_ledger.to_dict()
    else:
        budget_error = None
    if execution.error:
        execution_data["error_code"] = getattr(execution.error, "code", type(execution.error).__name__.upper())
    if not persist_stage("execution", execution_ref, execution_data):
        return terminal(OrchestrationResult(OrchestrationStatus.BLOCKED, (OrchestrationReason.LIFECYCLE_PERSISTENCE_FAILED,), execution.run_id, execution=execution, plan=plan))
    if budget_error is not None:
        return terminal(OrchestrationResult(OrchestrationStatus.BLOCKED, (budget_error,), execution.run_id, execution=execution, plan=plan))
    if execution.outcome is ExecutionOutcome.NOT_EXECUTED:
        return terminal(OrchestrationResult(OrchestrationStatus.NOT_EXECUTED, (OrchestrationReason.EXECUTOR_NOT_EXECUTED,), execution.run_id, execution=execution, plan=plan))
    if execution.outcome is ExecutionOutcome.BLOCKED:
        return terminal(OrchestrationResult(OrchestrationStatus.BLOCKED, (OrchestrationReason.EXECUTOR_BLOCKED,), execution.run_id, execution=execution, plan=plan))
    if execution.outcome is ExecutionOutcome.FAILED:
        return terminal(OrchestrationResult(OrchestrationStatus.BLOCKED, (OrchestrationReason.EXECUTOR_FAILED,), execution.run_id, execution=execution, plan=plan))

    progress = progress_observer.assess(execution)
    if progress.status is ProgressStatus.NO_PROGRESS:
        return terminal(OrchestrationResult(OrchestrationStatus.BLOCKED, (OrchestrationReason.NO_PROGRESS,), execution.run_id, execution=execution, plan=plan, progress=progress))
    if progress.status is ProgressStatus.UNKNOWN:
        return terminal(OrchestrationResult(OrchestrationStatus.INDETERMINATE, (OrchestrationReason.PROGRESS_UNKNOWN,), execution.run_id, execution=execution, plan=plan, progress=progress))

    verification = verifier.verify(execution)
    if not persist_stage("verification", verification.reference, {"verification_state": verification.state.value}):
        return terminal(OrchestrationResult(OrchestrationStatus.BLOCKED, (OrchestrationReason.LIFECYCLE_PERSISTENCE_FAILED,), execution.run_id, execution=execution, plan=plan, progress=progress, verification=verification))
    if verification.state is VerificationState.BLOCKED:
        return terminal(OrchestrationResult(OrchestrationStatus.BLOCKED, (OrchestrationReason.VERIFICATION_BLOCKED,), execution.run_id, execution=execution, plan=plan, progress=progress, verification=verification))
    if verification.state in (VerificationState.INDETERMINATE, VerificationState.NOT_EXECUTED):
        return terminal(OrchestrationResult(OrchestrationStatus.INDETERMINATE, (OrchestrationReason.VERIFICATION_UNKNOWN,), execution.run_id, execution=execution, plan=plan, progress=progress, verification=verification))
    if verification.state is VerificationState.FAIL:
        return terminal(OrchestrationResult(OrchestrationStatus.REJECTED, (OrchestrationReason.ACCEPTANCE_DECISION,), execution.run_id, execution=execution, plan=plan, progress=progress, verification=verification))

    acceptance = acceptance_authority.decide(verification)
    if not persist_stage("acceptance", acceptance.reference, {"acceptance_decision": acceptance.decision.value}):
        return terminal(OrchestrationResult(OrchestrationStatus.BLOCKED, (OrchestrationReason.LIFECYCLE_PERSISTENCE_FAILED,), execution.run_id, execution=execution, plan=plan, progress=progress, verification=verification, acceptance=acceptance))
    status = orchestration_status_for_acceptance(acceptance.decision)
    return terminal(OrchestrationResult(status, (OrchestrationReason.ACCEPTANCE_DECISION,), execution.run_id, execution=execution, plan=plan, progress=progress, verification=verification, acceptance=acceptance))
