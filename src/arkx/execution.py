"""Executor-neutral execution boundary contracts.

These protocols describe capability boundaries only. They do not select a
provider, invoke a model, create a sandbox, verify a patch, or accept a task.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
from typing import Any, Mapping, Protocol

from .harness import ErrorDomain, ErrorEnvelope, Retryability, RunState, derive_attempt_id, validate_transition
from .integration import AdapterIdentity, AdapterPreflight, CapabilityProvenance, IntegrationKind
from .harness import AcceptanceEvidence, VerificationEvidence
from .configuration import ConfigurationSnapshot


@dataclass(frozen=True)
class ExecutionBudgetSpec:
    """Executor-neutral budget declaration carried by an execution plan."""

    max_attempts: int | None = None
    max_tokens: int | None = None
    max_wall_time_ms: int | None = None
    max_cost: Decimal | None = None
    max_executor_invocations: int | None = None

    def __post_init__(self) -> None:
        for name in ("max_attempts", "max_tokens", "max_wall_time_ms", "max_executor_invocations"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.max_cost is not None and self.max_cost < 0:
            raise ValueError("max_cost must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_attempts": self.max_attempts,
            "max_tokens": self.max_tokens,
            "max_wall_time_ms": self.max_wall_time_ms,
            "max_cost": None if self.max_cost is None else str(self.max_cost),
            "max_executor_invocations": self.max_executor_invocations,
        }

    def digest(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class BudgetConsumption:
    accepted: bool
    reason: str
    ledger: "BudgetLedger"


@dataclass(frozen=True)
class BudgetLedger:
    """Immutable execution-budget ledger with idempotent attempt consumption."""

    budget: ExecutionBudgetSpec
    consumed_attempts: tuple[str, ...] = ()
    tokens_used: int = 0
    wall_time_ms_used: int = 0
    cost_used: Decimal = Decimal("0")
    executor_invocations_used: int = 0

    def __post_init__(self) -> None:
        if any(not attempt.strip() for attempt in self.consumed_attempts):
            raise ValueError("consumed attempt ids must be non-empty")
        if len(set(self.consumed_attempts)) != len(self.consumed_attempts):
            raise ValueError("consumed attempt ids must be unique")
        if min(self.tokens_used, self.wall_time_ms_used, self.executor_invocations_used) < 0 or self.cost_used < 0:
            raise ValueError("budget usage must be non-negative")
        object.__setattr__(self, "consumed_attempts", tuple(sorted(self.consumed_attempts)))

    def consume(self, attempt_id: str, *, tokens: int = 0, wall_time_ms: int = 0, cost: Decimal = Decimal("0"), executor_invocations: int = 1) -> BudgetConsumption:
        if not attempt_id.strip():
            raise ValueError("attempt_id must be non-empty")
        if min(tokens, wall_time_ms, executor_invocations) < 0 or cost < 0:
            raise ValueError("consumption values must be non-negative")
        if attempt_id in self.consumed_attempts:
            return BudgetConsumption(True, "ALREADY_CONSUMED", self)
        next_values = {
            "tokens": self.tokens_used + tokens,
            "wall_time_ms": self.wall_time_ms_used + wall_time_ms,
            "cost": self.cost_used + cost,
            "executor_invocations": self.executor_invocations_used + executor_invocations,
        }
        limits = (("tokens", self.budget.max_tokens), ("wall_time_ms", self.budget.max_wall_time_ms), ("cost", self.budget.max_cost), ("executor_invocations", self.budget.max_executor_invocations), ("attempts", self.budget.max_attempts))
        for name, limit in limits:
            value = len(self.consumed_attempts) + 1 if name == "attempts" else next_values[name]
            if limit is not None and value > limit:
                return BudgetConsumption(False, f"{name.upper()}_EXCEEDED", self)
        ledger = BudgetLedger(self.budget, self.consumed_attempts + (attempt_id,), next_values["tokens"], next_values["wall_time_ms"], next_values["cost"], next_values["executor_invocations"])
        return BudgetConsumption(True, "CONSUMED", ledger)

    def record_usage(self, attempt_id: str, *, tokens: int = 0, wall_time_ms: int = 0, cost: Decimal = Decimal("0")) -> BudgetConsumption:
        """Record measured post-execution usage for an already consumed attempt."""
        if attempt_id not in self.consumed_attempts:
            raise ValueError("usage must reference a consumed attempt")
        if min(tokens, wall_time_ms) < 0 or cost < 0:
            raise ValueError("usage values must be non-negative")
        next_values = {"tokens": self.tokens_used + tokens, "wall_time_ms": self.wall_time_ms_used + wall_time_ms, "cost": self.cost_used + cost}
        for name, limit in (("tokens", self.budget.max_tokens), ("wall_time_ms", self.budget.max_wall_time_ms), ("cost", self.budget.max_cost)):
            if limit is not None and next_values[name] > limit:
                return BudgetConsumption(False, f"{name.upper()}_EXCEEDED", self)
        ledger = BudgetLedger(self.budget, self.consumed_attempts, next_values["tokens"], next_values["wall_time_ms"], next_values["cost"], self.executor_invocations_used)
        return BudgetConsumption(True, "USAGE_RECORDED", ledger)

    def to_dict(self) -> dict[str, Any]:
        return {"budget_digest": self.budget.digest(), "budget": self.budget.to_dict(), "consumed_attempts": list(self.consumed_attempts), "tokens_used": self.tokens_used, "wall_time_ms_used": self.wall_time_ms_used, "cost_used": str(self.cost_used), "executor_invocations_used": self.executor_invocations_used}


@dataclass(frozen=True)
class RetryDecision:
    allowed: bool
    reason: str
    next_attempt: int | None = None


@dataclass(frozen=True)
class RetryAttemptPlan:
    trial_id: str
    previous_attempt_id: str
    previous_attempt_number: int
    next_attempt_id: str
    next_attempt_number: int
    configuration_digest: str

    def __post_init__(self) -> None:
        if self.previous_attempt_number < 1 or self.next_attempt_number != self.previous_attempt_number + 1:
            raise ValueError("retry attempt numbers must be consecutive and positive")
        expected_previous = derive_attempt_id(trial_id=self.trial_id, attempt_number=self.previous_attempt_number, configuration_digest=self.configuration_digest)
        expected_next = derive_attempt_id(trial_id=self.trial_id, attempt_number=self.next_attempt_number, configuration_digest=self.configuration_digest)
        if self.previous_attempt_id != expected_previous or self.next_attempt_id != expected_next:
            raise ValueError("retry attempt identity does not match trial and configuration")

    def to_dict(self) -> dict[str, Any]:
        return {
            "trial_id": self.trial_id,
            "previous_attempt_id": self.previous_attempt_id,
            "previous_attempt_number": self.previous_attempt_number,
            "next_attempt_id": self.next_attempt_id,
            "next_attempt_number": self.next_attempt_number,
            "configuration_digest": self.configuration_digest,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class RetryPolicy:
    """Pure retry authorization; it never performs a retry or changes state."""

    max_retries: int = 0
    allowed_domains: tuple[ErrorDomain, ...] = ()

    def __post_init__(self) -> None:
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        object.__setattr__(self, "allowed_domains", tuple(sorted(set(self.allowed_domains), key=lambda item: item.value)))

    def decide(self, error: ErrorEnvelope | None, *, retries_used: int, max_attempts: int | None = None) -> RetryDecision:
        if retries_used < 0:
            raise ValueError("retries_used must be non-negative")
        if error is None:
            return RetryDecision(False, "NO_ERROR")
        if error.retryability is not Retryability.RETRYABLE:
            return RetryDecision(False, "ERROR_NOT_RETRYABLE")
        if self.allowed_domains and error.domain not in self.allowed_domains:
            return RetryDecision(False, "ERROR_DOMAIN_NOT_ALLOWED")
        if retries_used >= self.max_retries:
            return RetryDecision(False, "RETRY_POLICY_EXHAUSTED")
        next_attempt = retries_used + 2
        if max_attempts is not None and next_attempt > max_attempts:
            return RetryDecision(False, "EXECUTION_BUDGET_EXHAUSTED")
        return RetryDecision(True, "RETRY_AUTHORIZED", next_attempt)


def plan_retry_attempt(
    *, trial_id: str, previous_attempt_id: str, previous_attempt_number: int,
    configuration_digest: str, decision: RetryDecision,
) -> RetryAttemptPlan | None:
    if not decision.allowed:
        return None
    if decision.next_attempt is None:
        raise ValueError("authorized retry must contain next_attempt")
    return RetryAttemptPlan(
        trial_id, previous_attempt_id, previous_attempt_number,
        derive_attempt_id(trial_id=trial_id, attempt_number=decision.next_attempt, configuration_digest=configuration_digest),
        decision.next_attempt, configuration_digest,
    )


@dataclass(frozen=True)
class CapabilityProfile:
    """Evidence-bearing, versioned capability declaration for one component."""

    subject_type: str
    subject_id: str
    version: str | None = None
    configuration_digest: str | None = None
    capabilities: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.subject_type.strip() or not self.subject_id.strip():
            raise ValueError("capability profile identity must be non-empty")
        if any(not value.strip() for value in self.capabilities):
            raise ValueError("capability names must be non-empty")
        if any(not value.strip() for value in self.evidence_refs):
            raise ValueError("capability evidence references must be non-empty")
        object.__setattr__(self, "capabilities", tuple(sorted(set(self.capabilities))))
        object.__setattr__(self, "evidence_refs", tuple(sorted(set(self.evidence_refs))))

    def supports(self, required: tuple[str, ...]) -> bool:
        return set(required).issubset(self.capabilities)

    def to_dict(self) -> dict[str, Any]:
        return {"subject_type": self.subject_type, "subject_id": self.subject_id, "version": self.version, "configuration_digest": self.configuration_digest, "capabilities": list(self.capabilities), "evidence_refs": list(self.evidence_refs)}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class CapabilityRegistry:
    profiles: tuple[CapabilityProfile, ...] = ()

    def __post_init__(self) -> None:
        values = tuple(sorted(self.profiles, key=lambda item: (item.subject_type, item.subject_id, item.version or "")))
        identities = [(item.subject_type, item.subject_id, item.version, item.configuration_digest) for item in values]
        if len(set(identities)) != len(identities):
            raise ValueError("capability profiles must have unique identities")
        object.__setattr__(self, "profiles", values)

    def find(self, subject_type: str, subject_id: str) -> tuple[CapabilityProfile, ...]:
        return tuple(item for item in self.profiles if item.subject_type == subject_type and item.subject_id == subject_id)

    def to_dict(self) -> dict[str, Any]:
        return {"profiles": [item.to_dict() for item in self.profiles]}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def digest(self) -> str:
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()[:16]

    @property
    def reference(self) -> str:
        return f"capability://{self.digest()}"


@dataclass(frozen=True)
class ExecutionRequest:
    task_id: str
    task_revision: str | None
    treatment: str
    prompt: str
    executor_id: str
    provider_id: str | None
    model_id: str | None
    sandbox_id: str | None
    budget_digest: str | None
    configuration_digest: str | None


@dataclass(frozen=True)
class ExecutionPlan:
    plan_id: str
    task_id: str
    task_revision: str | None
    treatment: str
    executor_id: str
    provider_id: str | None
    model_id: str | None
    sandbox_id: str | None
    budget_digest: str | None
    configuration_digest: str | None
    steps: tuple[str, ...] = ()
    budget: ExecutionBudgetSpec | None = None
    required_capabilities: tuple[str, ...] = ()
    minimum_capability_provenance: CapabilityProvenance = CapabilityProvenance.DECLARED
    configuration_snapshot: ConfigurationSnapshot | None = None
    provider_identity: AdapterIdentity | None = None
    sandbox_identity: AdapterIdentity | None = None

    def __post_init__(self) -> None:
        for value, name in ((self.plan_id, "plan_id"), (self.task_id, "task_id"), (self.treatment, "treatment"), (self.executor_id, "executor_id")):
            if not value or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        if any(not step.strip() for step in self.steps):
            raise ValueError("execution plan steps must be non-empty")
        object.__setattr__(self, "steps", tuple(self.steps))
        if any(not capability.strip() for capability in self.required_capabilities):
            raise ValueError("execution plan capabilities must be non-empty")
        object.__setattr__(self, "required_capabilities", tuple(sorted(set(self.required_capabilities))))
        if self.budget is not None:
            expected_digest = self.budget.digest()
            if self.budget_digest is None:
                object.__setattr__(self, "budget_digest", expected_digest)
            elif self.budget_digest != expected_digest:
                raise ValueError("execution plan budget_digest does not match budget")
        if self.configuration_snapshot is not None:
            expected_digest = self.configuration_snapshot.digest()
            if self.configuration_digest is None:
                object.__setattr__(self, "configuration_digest", expected_digest)
            elif self.configuration_digest != expected_digest:
                raise ValueError("execution plan configuration_digest does not match snapshot")
        for identity, expected_kind, expected_id, label in (
            (self.provider_identity, IntegrationKind.PROVIDER, self.provider_id, "provider"),
            (self.sandbox_identity, IntegrationKind.SANDBOX, self.sandbox_id, "sandbox"),
        ):
            if identity is None:
                continue
            if identity.kind is not expected_kind:
                raise ValueError(f"{label} identity has wrong integration kind")
            if expected_id is not None and identity.name != expected_id:
                raise ValueError(f"{label} identity does not match plan id")
            if identity.version is None or identity.configuration_digest is None:
                raise ValueError(f"{label} identity requires version and configuration_digest")

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "task_id": self.task_id,
            "task_revision": self.task_revision,
            "treatment": self.treatment,
            "executor_id": self.executor_id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "sandbox_id": self.sandbox_id,
            "budget_digest": self.budget_digest,
            "configuration_digest": self.configuration_digest,
            "steps": list(self.steps),
            "budget": None if self.budget is None else self.budget.to_dict(),
            "required_capabilities": list(self.required_capabilities),
            "minimum_capability_provenance": self.minimum_capability_provenance.value,
            "configuration_snapshot": None if self.configuration_snapshot is None else self.configuration_snapshot.to_dict(),
            "provider_identity": None if self.provider_identity is None else self.provider_identity.to_dict(),
            "sandbox_identity": None if self.sandbox_identity is None else self.sandbox_identity.to_dict(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def to_request(self, prompt: str) -> ExecutionRequest:
        return ExecutionRequest(
            self.task_id, self.task_revision, self.treatment, prompt,
            self.executor_id, self.provider_id, self.model_id, self.sandbox_id,
            self.budget_digest, self.configuration_digest,
        )

    def validate_capabilities(self, preflight: AdapterPreflight):
        """Apply routing capability policy before execution starts."""
        from .routing import assess_capability_policy
        return assess_capability_policy(
            preflight,
            self.required_capabilities,
            minimum_provenance=self.minimum_capability_provenance,
        )

    def preflight_matches_identity(self, preflight: AdapterPreflight) -> bool:
        """Check that a preflight describes this plan's executor/configuration."""
        return (
            preflight.identity.name == self.executor_id
            and preflight.identity.kind.value == "EXECUTOR"
            and (
                self.configuration_digest is None
                or preflight.identity.configuration_digest == self.configuration_digest
            )
        )

    def preflight_matches_integration(self, preflight: AdapterPreflight, kind: IntegrationKind) -> bool:
        """Check a provider or sandbox preflight against the plan binding."""
        expected = self.provider_identity if kind is IntegrationKind.PROVIDER else self.sandbox_identity if kind is IntegrationKind.SANDBOX else None
        expected_id = self.provider_id if kind is IntegrationKind.PROVIDER else self.sandbox_id if kind is IntegrationKind.SANDBOX else None
        return expected is not None and preflight.identity.kind is kind and preflight.identity.name == expected_id and preflight.identity.version == expected.version and preflight.identity.configuration_digest == expected.configuration_digest

    @property
    def reference(self) -> str:
        return f"plan://{self.plan_id}"


@dataclass(frozen=True)
class ExecutionResult:
    state: RunState
    artifact_refs: tuple[str, ...] = ()
    output: str | None = None
    usage: Mapping[str, Any] | None = None
    error: ErrorEnvelope | None = None

    def __post_init__(self) -> None:
        if self.state in {RunState.FAILED, RunState.BLOCKED} and self.error is None:
            raise ValueError("failed or blocked execution requires an error envelope")
        if self.state is RunState.COMPLETED and self.error is not None:
            raise ValueError("completed execution cannot contain an error envelope")
        refs = tuple(sorted(set(self.artifact_refs)))
        if any(not ref.strip() for ref in refs):
            raise ValueError("execution artifact references must be non-empty")
        object.__setattr__(self, "artifact_refs", refs)


def execution_reference(attempt_id: str) -> str:
    if not attempt_id.strip():
        raise ValueError("attempt_id must be non-empty")
    return f"execution://{attempt_id}"


def validate_execution_chain(plan: ExecutionPlan, *, plan_reference: str, execution_ref: str, attempt_id: str) -> None:
    if plan_reference != plan.reference:
        raise ValueError("plan reference does not match execution plan")
    if execution_ref != execution_reference(attempt_id):
        raise ValueError("execution reference does not match attempt")


@dataclass(frozen=True)
class ContractRun:
    request: ExecutionRequest
    result: ExecutionResult
    state_history: tuple[RunState, ...]
    verification: VerificationEvidence | None = None
    acceptance: AcceptanceEvidence | None = None
    budget_ledger: BudgetLedger | None = None
    budget_reason: str | None = None

    @classmethod
    def execute(cls, request: ExecutionRequest, executor: "Executor") -> "ContractRun":
        result = executor.execute(request)
        terminal = result.state
        history = (RunState.PLANNED, RunState.STARTED, RunState.EXECUTING, terminal)
        for previous, current in zip(history, history[1:]):
            validate_transition(previous, current)
        return cls(request, result, history)

    @classmethod
    def execute_with_budget(
        cls,
        request: ExecutionRequest,
        executor: "Executor",
        ledger: BudgetLedger,
        *,
        attempt_id: str,
        tokens: int = 0,
        wall_time_ms: int = 0,
        cost: Decimal = Decimal("0"),
        executor_invocations: int = 1,
    ) -> "ContractRun":
        consumption = ledger.consume(
            attempt_id,
            tokens=tokens,
            wall_time_ms=wall_time_ms,
            cost=cost,
            executor_invocations=executor_invocations,
        )
        if not consumption.accepted:
            error = ErrorEnvelope(ErrorDomain.HARNESS, consumption.reason, "execution budget rejected attempt", Retryability.NOT_RETRYABLE, attempt_number=None)
            result = ExecutionResult(RunState.BLOCKED, error=error)
            return cls(request, result, (RunState.PLANNED, RunState.BLOCKED), budget_ledger=consumption.ledger, budget_reason=consumption.reason)
        run = cls.execute(request, executor)
        return cls(run.request, run.result, run.state_history, run.verification, run.acceptance, consumption.ledger, consumption.reason)

    def with_verification(self, evidence: VerificationEvidence) -> "ContractRun":
        return ContractRun(self.request, self.result, self.state_history, evidence, self.acceptance)

    def with_acceptance(self, evidence: AcceptanceEvidence) -> "ContractRun":
        return ContractRun(self.request, self.result, self.state_history, self.verification, evidence)

    def is_accepted(self) -> bool:
        return (
            self.result.state is RunState.COMPLETED
            and self.verification is not None
            and self.verification.state == "PASS"
            and self.acceptance is not None
            and self.acceptance.decision == "ACCEPTED"
        )


@dataclass(frozen=True)
class ProviderRequest:
    prompt: str
    model_id: str
    configuration_digest: str | None
    budget_digest: str | None


@dataclass(frozen=True)
class ProviderResponse:
    output: str | None
    usage: Mapping[str, Any] | None = None
    error: ErrorEnvelope | None = None


@dataclass(frozen=True)
class SandboxRequest:
    task_id: str
    task_revision: str | None
    sandbox_id: str
    policy_digest: str | None


class Executor(Protocol):
    executor_id: str

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute one request without deciding verification or acceptance."""


class Provider(Protocol):
    provider_identity: AdapterIdentity

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        """Return provider output or a structured provider error."""


def validate_provider_identity(provider: Provider) -> AdapterIdentity:
    """Require a versioned, configuration-bound provider identity."""
    identity = getattr(provider, "provider_identity", None)
    if not isinstance(identity, AdapterIdentity) or identity.kind is not IntegrationKind.PROVIDER:
        raise ValueError("provider must expose an AdapterIdentity with PROVIDER kind")
    if identity.version is None or identity.configuration_digest is None:
        raise ValueError("provider identity requires version and configuration_digest")
    return identity


class Sandbox(Protocol):
    sandbox_identity: AdapterIdentity

    def prepare(self, request: SandboxRequest) -> None:
        """Prepare an isolated workspace according to the declared policy."""

    def collect_artifacts(self) -> tuple[str, ...]:
        """Return references to artifacts produced by the sandbox."""


def validate_sandbox_identity(sandbox: Sandbox) -> AdapterIdentity:
    """Require a versioned, configuration-bound sandbox identity."""
    identity = getattr(sandbox, "sandbox_identity", None)
    if not isinstance(identity, AdapterIdentity) or identity.kind is not IntegrationKind.SANDBOX:
        raise ValueError("sandbox must expose an AdapterIdentity with SANDBOX kind")
    if identity.version is None or identity.configuration_digest is None:
        raise ValueError("sandbox identity requires version and configuration_digest")
    return identity


class FakeExecutor:
    """Deterministic contract-test executor; it has no external dependencies."""

    executor_id = "fake-executor"

    def __init__(self, result: ExecutionResult) -> None:
        self.result = result
        self.requests: list[ExecutionRequest] = []

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        self.requests.append(request)
        return self.result


class FakeProvider:
    provider_identity = AdapterIdentity(IntegrationKind.PROVIDER, "fake-provider", "1", "fake-config")
    provider_id = "fake-provider"

    def __init__(self, response: ProviderResponse) -> None:
        self.response = response
        self.requests: list[ProviderRequest] = []

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        self.requests.append(request)
        return self.response


class FakeSandbox:
    sandbox_identity = AdapterIdentity(IntegrationKind.SANDBOX, "fake-sandbox", "1", "fake-config")
    sandbox_id = "fake-sandbox"

    def __init__(self, artifacts: tuple[str, ...] = ()) -> None:
        self.artifacts = artifacts
        self.requests: list[SandboxRequest] = []

    def prepare(self, request: SandboxRequest) -> None:
        self.requests.append(request)

    def collect_artifacts(self) -> tuple[str, ...]:
        return self.artifacts
