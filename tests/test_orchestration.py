import unittest
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from arkx.characterization import RecommendedPath, TaskCharacterization, TaskSignals, characterize
from arkx.orchestration import (
    ExecutionOutcome,
    ExecutionResult,
    OrchestrationReason,
    OrchestrationStatus,
    orchestration_status_for_acceptance,
    orchestration_status_for_execution,
    run_routed_pipeline,
)
from arkx.p82_baseline import AcceptanceDecision, AcceptanceResult, VerificationResult, VerificationState
from arkx.progress import ProgressAssessment, ProgressEvidence, ProgressStatus, Confidence
from arkx.request import ArkxRequest, GovernancePolicy, RequestBudget, RequestEnvironment, authorize_request
from arkx.routing import RoutingDecision, RoutingDecisionType, RoutingBudget
from arkx.selection import ExecutorBinding, ExecutorRegistry, SelectionStatus, TreatmentDefinition, select_executor, select_treatment
from arkx.executor_qualification import ExecutorIdentity, QualificationStatus
from arkx.execution import ExecutionResult as ContractExecutionResult, FakeExecutor as ContractFakeExecutor
from arkx.harness import RunState
from arkx.orchestration import ContractExecutorRunner
from arkx.orchestration import legacy_execution_from_contract
from arkx.orchestration import build_execution_plan
from arkx.configuration import ConfigurationSnapshot
from arkx.verifier import CommandVerifier, VerificationEvidenceStore


def setup():
    request = ArkxRequest(
        "req-1", "task-1", "developer",
        TaskSignals(("src/a.py",), (), ("a",), ("tests/a.py",), (), (), ("tests",)),
        ("src",), RequestBudget(2, 1000, 10000), RequestEnvironment("local", "workspace", "HEAD"), "authority-1",
    )
    governance = authorize_request(request, GovernancePolicy("gov", ("developer",), ("local",), 3, 2000, 20000))
    characterization = characterize(request.signals)
    treatment = TreatmentDefinition("simple", RecommendedPath.SIMPLE_PATH, ())
    selection = select_executor(treatment, ExecutorRegistry((ExecutorBinding(ExecutorIdentity("mini", "1", "adapter", "digest"), ("edit",), QualificationStatus.QUALIFIABLE, ("evidence://1",)),)))
    routing = RoutingDecision(1, "task-1", RecommendedPath.SIMPLE_PATH, RecommendedPath.SIMPLE_PATH, RoutingDecisionType.ROUTE, characterization.confidence, (), None, "test", RoutingBudget())
    return governance, characterization, routing, selection


class FakeExecutor:
    def __init__(self, outcome=ExecutionOutcome.COMPLETED): self.outcome = outcome
    def run(self, request, selection): return ExecutionResult("run-1", self.outcome, telemetry={"total_tokens": 0, "wall_time_ms": 0, "cost": 0})
    def run_with_budget(self, request, selection, *, attempt_id, budget_ledger): return self.run(request, selection)


class FakeProgress:
    def __init__(self, status=ProgressStatus.PROGRESS_PROVEN): self.status = status
    def assess(self, execution):
        evidence = ProgressEvidence((), (), (), None, None, None, None)
        return ProgressAssessment(1, self.status, Confidence.HIGH, (), (), None, {}, evidence)


class FakeVerifier:
    def __init__(self, state=VerificationState.PASS): self.state = state
    def verify(self, execution): return VerificationResult(self.state, "verifier-1", (), (), ("evidence://verify",))


class FakeAcceptance:
    identity = "authority-1"
    def __init__(self, decision=AcceptanceDecision.ACCEPTED): self.decision = decision
    def decide(self, verification): return AcceptanceResult(self.decision, self.identity, "raw", verification.evidence)


class OrchestrationTests(unittest.TestCase):
    def test_state_crosswalk_is_total_and_explicit(self):
        self.assertEqual(orchestration_status_for_execution(ExecutionOutcome.COMPLETED), OrchestrationStatus.EXECUTED)
        self.assertEqual(orchestration_status_for_execution(ExecutionOutcome.FAILED), OrchestrationStatus.BLOCKED)
        self.assertEqual(orchestration_status_for_execution(ExecutionOutcome.BLOCKED), OrchestrationStatus.BLOCKED)
        self.assertEqual(orchestration_status_for_execution(ExecutionOutcome.NOT_EXECUTED), OrchestrationStatus.NOT_EXECUTED)
        for decision, expected in ((AcceptanceDecision.ACCEPTED, OrchestrationStatus.ACCEPTED), (AcceptanceDecision.REJECTED, OrchestrationStatus.REJECTED), (AcceptanceDecision.BLOCKED, OrchestrationStatus.BLOCKED), (AcceptanceDecision.NOT_EXECUTED, OrchestrationStatus.NOT_EXECUTED), (AcceptanceDecision.INDETERMINATE, OrchestrationStatus.INDETERMINATE)):
            self.assertEqual(orchestration_status_for_acceptance(decision), expected)
    def test_pipeline_runs_in_order_to_acceptance(self):
        governance, characterization, routing, selection = setup()
        result = run_routed_pipeline(governance, characterization, routing, selection, FakeExecutor(), FakeProgress(), FakeVerifier(), FakeAcceptance())
        self.assertEqual(result.status, OrchestrationStatus.ACCEPTED)
        self.assertIsNotNone(result.verification)
        self.assertIsNotNone(result.acceptance)

    def test_pipeline_uses_persisted_command_verifier_before_acceptance(self):
        governance, characterization, routing, selection = setup()
        with TemporaryDirectory() as directory:
            verifier = CommandVerifier(
                authority="authority-1",
                workspace=directory,
                command=(sys.executable, "-c", "print('pipeline-verified')"),
                test_id="pipeline-smoke",
                evidence_store=VerificationEvidenceStore(directory + "/evidence"),
            )
            result = run_routed_pipeline(governance, characterization, routing, selection, FakeExecutor(), FakeProgress(), verifier, FakeAcceptance())
            files = list((Path(directory) / "evidence" / "run-1").glob("verification-*.json"))
            content = files[0].read_text(encoding="utf-8")
        self.assertEqual(result.status, OrchestrationStatus.ACCEPTED)
        self.assertEqual(len(files), 1)
        self.assertIn("pipeline-verified", content)

    def test_invalid_governance_blocks_before_executor(self):
        governance, characterization, routing, selection = setup()
        blocked = governance.__class__(governance.request_id, governance.status.BLOCKED, governance.authority_id, (), None)
        result = run_routed_pipeline(blocked, characterization, routing, selection, FakeExecutor(), FakeProgress(), FakeVerifier(), FakeAcceptance())
        self.assertEqual(result.status, OrchestrationStatus.BLOCKED)
        self.assertIn(OrchestrationReason.GOVERNANCE_REQUIRED, result.reason_codes)

    def test_no_progress_blocks_without_verification(self):
        governance, characterization, routing, selection = setup()
        result = run_routed_pipeline(governance, characterization, routing, selection, FakeExecutor(), FakeProgress(ProgressStatus.NO_PROGRESS), FakeVerifier(), FakeAcceptance())
        self.assertEqual(result.status, OrchestrationStatus.BLOCKED)
        self.assertIsNone(result.verification)

    def test_acceptance_authority_mismatch_blocks(self):
        governance, characterization, routing, selection = setup()
        authority = FakeAcceptance(); authority.identity = "other"
        result = run_routed_pipeline(governance, characterization, routing, selection, FakeExecutor(), FakeProgress(), FakeVerifier(), authority)
        self.assertIn(OrchestrationReason.ACCEPTANCE_AUTHORITY_MISMATCH, result.reason_codes)

    def test_executor_failure_is_not_acceptance_rejection(self):
        governance, characterization, routing, selection = setup()
        result = run_routed_pipeline(governance, characterization, routing, selection, FakeExecutor(ExecutionOutcome.FAILED), FakeProgress(), FakeVerifier(), FakeAcceptance())
        self.assertEqual(result.status, OrchestrationStatus.BLOCKED)

    def test_serialization_is_deterministic(self):
        governance, characterization, routing, selection = setup()
        first = run_routed_pipeline(governance, characterization, routing, selection, FakeExecutor(), FakeProgress(), FakeVerifier(), FakeAcceptance()).to_json()
        second = run_routed_pipeline(governance, characterization, routing, selection, FakeExecutor(), FakeProgress(), FakeVerifier(), FakeAcceptance()).to_json()
        self.assertEqual(first, second)

    def test_contract_executor_runner_bridges_neutral_executor(self):
        governance, characterization, routing, selection = setup()
        runner = ContractExecutorRunner(ContractFakeExecutor(ContractExecutionResult(RunState.COMPLETED, ("artifact://1",), usage={"total_tokens": 0, "wall_time_ms": 0, "cost": 0})))
        result = run_routed_pipeline(governance, characterization, routing, selection, runner, FakeProgress(), FakeVerifier(), FakeAcceptance())
        self.assertEqual(result.status, OrchestrationStatus.ACCEPTED)
        self.assertEqual(result.execution.outcome, ExecutionOutcome.COMPLETED)

    def test_contract_executor_runner_preserves_blocked(self):
        governance, characterization, routing, selection = setup()
        from arkx.harness import ErrorDomain, ErrorEnvelope, Retryability
        error = ErrorEnvelope(ErrorDomain.SANDBOX, "UNAVAILABLE", "sandbox unavailable", Retryability.NOT_RETRYABLE)
        runner = ContractExecutorRunner(ContractFakeExecutor(ContractExecutionResult(RunState.BLOCKED, error=error)))
        result = run_routed_pipeline(governance, characterization, routing, selection, runner, FakeProgress(), FakeVerifier(), FakeAcceptance())
        self.assertEqual(result.status, OrchestrationStatus.BLOCKED)

    def test_orchestration_accepts_neutral_executor_directly(self):
        governance, characterization, routing, selection = setup()
        executor = ContractFakeExecutor(ContractExecutionResult(RunState.COMPLETED, ("artifact://direct",), usage={"total_tokens": 0, "wall_time_ms": 0, "cost": 0}))
        result = run_routed_pipeline(governance, characterization, routing, selection, executor, FakeProgress(), FakeVerifier(), FakeAcceptance())
        self.assertEqual(result.status, OrchestrationStatus.ACCEPTED)
        self.assertEqual(result.execution.outcome, ExecutionOutcome.COMPLETED)

    def test_neutral_and_legacy_executor_paths_are_behaviorally_equivalent(self):
        governance, characterization, routing, selection = setup()
        neutral = ContractFakeExecutor(ContractExecutionResult(RunState.COMPLETED, ("artifact://same",), usage={"total_tokens": 0, "wall_time_ms": 0, "cost": 0}))
        bridged = ContractExecutorRunner(ContractFakeExecutor(ContractExecutionResult(RunState.COMPLETED, ("artifact://same",), usage={"total_tokens": 0, "wall_time_ms": 0, "cost": 0})))
        direct_result = run_routed_pipeline(governance, characterization, routing, selection, neutral, FakeProgress(), FakeVerifier(), FakeAcceptance())
        bridge_result = run_routed_pipeline(governance, characterization, routing, selection, bridged, FakeProgress(), FakeVerifier(), FakeAcceptance())
        self.assertEqual(direct_result.status, bridge_result.status)
        self.assertEqual(direct_result.execution.to_dict(), bridge_result.execution.to_dict())

    def test_orchestration_records_deterministic_execution_plan_before_execution(self):
        governance, characterization, routing, selection = setup()
        first = build_execution_plan(governance, routing, selection)
        second = build_execution_plan(governance, routing, selection)
        self.assertEqual(first.to_json(), second.to_json())
        result = run_routed_pipeline(governance, characterization, routing, selection, ContractFakeExecutor(ContractExecutionResult(RunState.COMPLETED, usage={"total_tokens": 0, "wall_time_ms": 0, "cost": 0})), FakeProgress(), FakeVerifier(), FakeAcceptance())
        self.assertEqual(result.plan, first)
        self.assertEqual(result.plan.budget_digest, first.budget_digest)
        self.assertEqual(first.required_capabilities, ())

    def test_orchestration_persists_optional_provider_and_sandbox_identities_in_plan(self):
        from arkx.integration import AdapterIdentity, IntegrationKind
        governance, characterization, routing, selection = setup()
        provider = AdapterIdentity(IntegrationKind.PROVIDER, "provider-a", "1", "provider-config")
        sandbox = AdapterIdentity(IntegrationKind.SANDBOX, "local", "1", "sandbox-config")
        plan = build_execution_plan(governance, routing, selection, provider_identity=provider, sandbox_identity=sandbox)
        self.assertEqual(plan.provider_identity, provider)
        self.assertEqual(plan.sandbox_identity, sandbox)

    def test_orchestration_requires_and_persists_provider_and_sandbox_preflights(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from arkx.event_log import EventLog, replay_chain
        from arkx.integration import AdapterIdentity, DependencyObservation, IntegrationKind, assess_preflight
        governance, characterization, routing, selection = setup()
        provider = AdapterIdentity(IntegrationKind.PROVIDER, "provider-a", "1", "provider-config")
        sandbox = AdapterIdentity(IntegrationKind.SANDBOX, "local", "1", "sandbox-config")
        provider_preflight = assess_preflight(provider, (DependencyObservation("provider", True, "1"),))
        sandbox_preflight = assess_preflight(sandbox, (DependencyObservation("runtime", True, "1"),))
        with TemporaryDirectory() as directory:
            log = EventLog(Path(directory) / "events.jsonl", run_id="run-1")
            result = run_routed_pipeline(governance, characterization, routing, selection, FakeExecutor(), FakeProgress(), FakeVerifier(), FakeAcceptance(), event_log=log, provider_identity=provider, sandbox_identity=sandbox, provider_preflight=provider_preflight, sandbox_preflight=sandbox_preflight)
            chain = replay_chain(log.read(), run_id="run-1")
        self.assertEqual(result.status, OrchestrationStatus.ACCEPTED)
        self.assertEqual(chain.provider_preflight_ref, provider_preflight.reference)
        self.assertEqual(chain.sandbox_preflight_ref, sandbox_preflight.reference)

    def test_orchestration_blocks_when_bound_provider_preflight_is_missing(self):
        from arkx.integration import AdapterIdentity, IntegrationKind
        governance, characterization, routing, selection = setup()
        provider = AdapterIdentity(IntegrationKind.PROVIDER, "provider-a", "1", "provider-config")
        result = run_routed_pipeline(governance, characterization, routing, selection, FakeExecutor(), FakeProgress(), FakeVerifier(), FakeAcceptance(), provider_identity=provider)
        self.assertIn(OrchestrationReason.PROVIDER_PREFLIGHT_REQUIRED, result.reason_codes)

    def test_capability_required_plan_blocks_before_executor_without_preflight(self):
        governance, characterization, routing, selection = setup()
        treatment = TreatmentDefinition("capability", RecommendedPath.SIMPLE_PATH, ("edit",))
        selection = selection.__class__(selection.status, selection.reason_codes, selection.path, treatment, selection.executor, selection.telemetry, selection.schema_version)
        executor = FakeExecutor()
        result = run_routed_pipeline(governance, characterization, routing, selection, executor, FakeProgress(), FakeVerifier(), FakeAcceptance())
        self.assertIn(OrchestrationReason.CAPABILITY_PREFLIGHT_REQUIRED, result.reason_codes)
        self.assertEqual(result.status, OrchestrationStatus.BLOCKED)

    def test_capability_required_plan_requires_preflight_event_log(self):
        governance, characterization, routing, selection = setup()
        treatment = TreatmentDefinition("capability", RecommendedPath.SIMPLE_PATH, ("edit",))
        selection = selection.__class__(selection.status, selection.reason_codes, selection.path, treatment, selection.executor, selection.telemetry, selection.schema_version)
        from arkx.integration import AdapterIdentity, CapabilityProvenance, DependencyObservation, IntegrationKind, assess_preflight
        preflight = assess_preflight(
            AdapterIdentity(IntegrationKind.EXECUTOR, "mini", "1", selection.executor.executor.configuration_digest),
            (DependencyObservation("runtime", True, "1"),),
            capabilities=("edit",), capability_digest="capability", capability_provenance=CapabilityProvenance.OBSERVED,
        )
        result = run_routed_pipeline(governance, characterization, routing, selection, FakeExecutor(), FakeProgress(), FakeVerifier(), FakeAcceptance(), capability_preflight=preflight)
        self.assertIn(OrchestrationReason.CAPABILITY_PREFLIGHT_PERSISTENCE_REQUIRED, result.reason_codes)

    def test_event_log_records_plan_execution_verification_and_acceptance(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from arkx.event_log import EventLog, replay_chain, replay_events
        governance, characterization, routing, selection = setup()
        with TemporaryDirectory() as directory:
            log = EventLog(Path(directory) / "events.jsonl", run_id="run-1")
            result = run_routed_pipeline(governance, characterization, routing, selection, FakeExecutor(), FakeProgress(), FakeVerifier(), FakeAcceptance(), event_log=log)
            chain = replay_chain(log.read(), run_id="run-1")
            replay = replay_events(log.read(), run_id="run-1")
        self.assertEqual(result.status, OrchestrationStatus.ACCEPTED)
        self.assertIsNotNone(chain.plan_ref)
        self.assertEqual(chain.execution_ref, "execution://run-1")
        self.assertEqual(chain.verification_ref, result.verification.reference)
        self.assertEqual(chain.acceptance_ref, result.acceptance.reference)
        self.assertEqual(replay.declared_status, "ACCEPTED")

    def test_lifecycle_persistence_failure_has_neutral_reason(self):
        governance, characterization, routing, selection = setup()
        class FailingLog:
            def append_stage(self, **kwargs):
                raise OSError("read-only event log")
        result = run_routed_pipeline(governance, characterization, routing, selection, FakeExecutor(), FakeProgress(), FakeVerifier(), FakeAcceptance(), event_log=FailingLog())
        self.assertIn(OrchestrationReason.LIFECYCLE_PERSISTENCE_FAILED, result.reason_codes)

    def test_legacy_result_is_only_a_deterministic_boundary_conversion(self):
        from arkx.harness import ErrorDomain, ErrorEnvelope, Retryability
        neutral = ContractExecutionResult(
            RunState.BLOCKED,
            ("artifact://blocked",),
            error=ErrorEnvelope(ErrorDomain.SANDBOX, "BLOCKED", "blocked", Retryability.UNKNOWN),
        )
        legacy = legacy_execution_from_contract(neutral)
        self.assertEqual(legacy.outcome, ExecutionOutcome.BLOCKED)
        self.assertEqual(legacy.evidence_refs, ("artifact://blocked",))

    def test_pipeline_blocks_before_runner_when_invocation_budget_is_zero(self):
        governance, characterization, routing, selection = setup()
        request = governance.request.__class__(
            governance.request.request_id, governance.request.task_id, governance.request.requester,
            governance.request.signals, governance.request.authorized_paths,
            RequestBudget(0, 1000, 10000),
            governance.request.environment, governance.request.acceptance_authority,
        )
        governance = authorize_request(request, GovernancePolicy("gov", ("developer",), ("local",), 3, 2000, 20000))
        class MustNotRun(FakeExecutor):
            def run(self, request, selection):
                raise AssertionError("runner must not be called after budget rejection")
        result = run_routed_pipeline(governance, characterization, routing, selection, MustNotRun(), FakeProgress(), FakeVerifier(), FakeAcceptance())
        self.assertIn(OrchestrationReason.EXECUTION_BUDGET_EXHAUSTED, result.reason_codes)

    def test_pipeline_blocks_after_execution_when_budget_measurement_is_missing(self):
        governance, characterization, routing, selection = setup()
        class NoUsage:
            def run(self, request, selection):
                return ExecutionResult("run-1", ExecutionOutcome.COMPLETED)
            def run_with_budget(self, request, selection, *, attempt_id, budget_ledger):
                return self.run(request, selection)
        result = run_routed_pipeline(governance, characterization, routing, selection, NoUsage(), FakeProgress(), FakeVerifier(), FakeAcceptance())
        self.assertIn(OrchestrationReason.BUDGET_USAGE_UNAVAILABLE, result.reason_codes)

    def test_pipeline_blocks_legacy_runner_without_budget_enforcement(self):
        governance, characterization, routing, selection = setup()
        class LegacyRunner:
            def run(self, request, selection):
                raise AssertionError("legacy runner must be blocked before execution")
        result = run_routed_pipeline(governance, characterization, routing, selection, LegacyRunner(), FakeProgress(), FakeVerifier(), FakeAcceptance())
        self.assertIn(OrchestrationReason.BUDGET_ENFORCEMENT_REQUIRED, result.reason_codes)

    def test_execution_plan_persists_typed_configuration_snapshot(self):
        governance, characterization, routing, selection = setup()
        snapshot = ConfigurationSnapshot("executor", "1", {"mode": "fake"})
        binding = selection.executor
        binding_executor = binding.executor.__class__(binding.executor.name, binding.executor.version, binding.executor.integration_kind, snapshot.digest(), binding.executor.advertised_capabilities)
        selection = selection.__class__(selection.status, selection.reason_codes, path=selection.path, treatment=selection.treatment, executor=binding.__class__(binding_executor, binding.capabilities, binding.qualification_status, binding.evidence_refs), telemetry=selection.telemetry)
        plan = build_execution_plan(governance, routing, selection, configuration_snapshot=snapshot)
        self.assertEqual(plan.configuration_snapshot, snapshot)
        self.assertEqual(plan.configuration_digest, snapshot.digest())


if __name__ == "__main__":
    unittest.main()
