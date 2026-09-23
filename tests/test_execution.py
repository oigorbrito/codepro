import unittest
from decimal import Decimal

from arkx.execution import (
    BudgetLedger,
    CapabilityProfile,
    CapabilityRegistry,
    ContractRun,
    ExecutionBudgetSpec,
    ExecutionRequest,
    ExecutionPlan,
    ExecutionResult,
    FakeExecutor,
    FakeProvider,
    FakeSandbox,
    ProviderRequest,
    ProviderResponse,
    RetryPolicy,
    RetryDecision,
    plan_retry_attempt,
    validate_execution_chain,
    validate_provider_identity,
    validate_sandbox_identity,
    SandboxRequest,
)
from arkx.harness import ErrorDomain, ErrorEnvelope, Retryability, RunState, derive_attempt_id
from arkx.integration import AdapterIdentity, CapabilityProvenance, DependencyObservation, IntegrationKind, assess_preflight
from arkx.configuration import ConfigurationSnapshot


class ExecutionContractTests(unittest.TestCase):
    def test_budget_ledger_consumes_each_attempt_once_and_is_immutable(self):
        ledger = BudgetLedger(ExecutionBudgetSpec(max_attempts=1, max_tokens=10))
        first = ledger.consume("attempt-1", tokens=4)
        duplicate = first.ledger.consume("attempt-1", tokens=4)
        self.assertTrue(first.accepted)
        self.assertEqual(duplicate.reason, "ALREADY_CONSUMED")
        self.assertEqual(duplicate.ledger.tokens_used, 4)
        self.assertEqual(ledger.tokens_used, 0)

    def test_budget_ledger_rejects_without_mutating_when_limit_exceeded(self):
        ledger = BudgetLedger(ExecutionBudgetSpec(max_attempts=1, max_tokens=100))
        first = ledger.consume("attempt-1", tokens=10)
        second = first.ledger.consume("attempt-2", tokens=1)
        self.assertFalse(second.accepted)
        self.assertEqual(second.reason, "ATTEMPTS_EXCEEDED")
        self.assertEqual(second.ledger.consumed_attempts, ("attempt-1",))

    def test_budget_ledger_records_measured_usage_after_consumption(self):
        ledger = BudgetLedger(ExecutionBudgetSpec(max_attempts=1, max_tokens=10))
        consumed = ledger.consume("attempt-1")
        measured = consumed.ledger.record_usage("attempt-1", tokens=4)
        self.assertTrue(measured.accepted)
        self.assertEqual(measured.ledger.tokens_used, 4)

    def test_budget_ledger_rejects_usage_without_consumed_attempt(self):
        ledger = BudgetLedger(ExecutionBudgetSpec(max_tokens=10))
        with self.assertRaises(ValueError):
            ledger.record_usage("missing", tokens=1)

    def test_contract_run_consumes_budget_before_executor(self):
        executor = FakeExecutor(ExecutionResult(RunState.COMPLETED))
        ledger = BudgetLedger(ExecutionBudgetSpec(max_attempts=1))
        run = ContractRun.execute_with_budget(self.request(), executor, ledger, attempt_id="attempt-1")
        self.assertEqual(run.result.state, RunState.COMPLETED)
        self.assertEqual(run.budget_ledger.consumed_attempts, ("attempt-1",))
        self.assertEqual(len(executor.requests), 1)

    def test_contract_run_blocks_before_executor_when_budget_is_exhausted(self):
        executor = FakeExecutor(ExecutionResult(RunState.COMPLETED))
        ledger = BudgetLedger(ExecutionBudgetSpec(max_attempts=0))
        run = ContractRun.execute_with_budget(self.request(), executor, ledger, attempt_id="attempt-1")
        self.assertEqual(run.result.state, RunState.BLOCKED)
        self.assertEqual(run.budget_reason, "ATTEMPTS_EXCEEDED")
        self.assertEqual(len(executor.requests), 0)

    def test_retry_policy_requires_retryable_error_and_respects_limits(self):
        policy = RetryPolicy(max_retries=1, allowed_domains=(ErrorDomain.PROVIDER,))
        error = ErrorEnvelope(ErrorDomain.PROVIDER, "TEMP", "temporary", Retryability.RETRYABLE)
        decision = policy.decide(error, retries_used=0, max_attempts=2)
        self.assertEqual((decision.allowed, decision.next_attempt), (True, 2))
        self.assertFalse(policy.decide(error, retries_used=1, max_attempts=2).allowed)

    def test_retry_policy_rejects_unknown_nonretryable_and_wrong_domain(self):
        policy = RetryPolicy(max_retries=2, allowed_domains=(ErrorDomain.PROVIDER,))
        unknown = ErrorEnvelope(ErrorDomain.PROVIDER, "UNKNOWN", "unknown")
        other = ErrorEnvelope(ErrorDomain.SANDBOX, "TEMP", "temporary", Retryability.RETRYABLE)
        self.assertEqual(policy.decide(unknown, retries_used=0).reason, "ERROR_NOT_RETRYABLE")
        self.assertEqual(policy.decide(other, retries_used=0).reason, "ERROR_DOMAIN_NOT_ALLOWED")

    def test_retry_attempt_plan_is_deterministic_and_preserves_previous_attempt(self):
        policy = RetryPolicy(max_retries=1)
        error = ErrorEnvelope(ErrorDomain.PROVIDER, "TEMP", "temporary", Retryability.RETRYABLE)
        decision = policy.decide(error, retries_used=0, max_attempts=2)
        previous = derive_attempt_id(trial_id="trial", attempt_number=1, configuration_digest="cfg")
        plan = plan_retry_attempt(trial_id="trial", previous_attempt_id=previous, previous_attempt_number=1, configuration_digest="cfg", decision=decision)
        self.assertEqual(plan.next_attempt_number, 2)
        self.assertEqual(plan.to_json(), plan_retry_attempt(trial_id="trial", previous_attempt_id=previous, previous_attempt_number=1, configuration_digest="cfg", decision=decision).to_json())

    def test_retry_attempt_plan_is_absent_when_retry_is_not_authorized(self):
        self.assertIsNone(plan_retry_attempt(trial_id="trial", previous_attempt_id="ignored", previous_attempt_number=1, configuration_digest="cfg", decision=RetryDecision(False, "BLOCKED")))

    def test_execution_budget_spec_is_validated_and_digest_is_stable(self):
        budget = ExecutionBudgetSpec(max_attempts=2, max_tokens=100, max_cost=Decimal("1.25"))
        equivalent = ExecutionBudgetSpec(max_attempts=2, max_tokens=100, max_cost=Decimal("1.25"))
        self.assertEqual(budget.digest(), equivalent.digest())
        with self.assertRaises(ValueError):
            ExecutionBudgetSpec(max_attempts=-1)

    def test_capability_profile_is_deterministic_and_evidence_bearing(self):
        profile = CapabilityProfile("provider", "provider-a", "v1", "cfg", ("completion", "completion"), ("artifact://cap",))
        equivalent = CapabilityProfile("provider", "provider-a", "v1", "cfg", ("completion",), ("artifact://cap",))
        self.assertEqual(profile.capabilities, ("completion",))
        self.assertEqual(profile.to_json(), equivalent.to_json())

    def test_capability_registry_digest_is_stable_and_referenced(self):
        first = CapabilityRegistry((CapabilityProfile("provider", "a", "v1", "cfg", ("completion",), ("evidence://cap",)),))
        second = CapabilityRegistry((CapabilityProfile("provider", "a", "v1", "cfg", ("completion",), ("evidence://cap",)),))
        self.assertEqual(first.digest(), second.digest())
        self.assertEqual(first.reference, f"capability://{first.digest()}")

    def test_capability_registry_orders_and_finds_profiles(self):
        registry = CapabilityRegistry((CapabilityProfile("sandbox", "b"), CapabilityProfile("provider", "a")))
        self.assertEqual([item.subject_type for item in registry.profiles], ["provider", "sandbox"])
        self.assertEqual(registry.find("provider", "a")[0].subject_id, "a")

    def test_capability_registry_rejects_duplicate_identity(self):
        with self.assertRaises(ValueError):
            CapabilityRegistry((CapabilityProfile("provider", "a"), CapabilityProfile("provider", "a")))

    def test_execution_plan_applies_capability_policy_before_execution(self):
        plan = ExecutionPlan(
            "plan-cap", "task", "rev", "A", "executor", None, None, "sandbox", None, "cfg",
            ("execute",), required_capabilities=("patch",),
            minimum_capability_provenance=CapabilityProvenance.OBSERVED,
        )
        preflight = assess_preflight(
            AdapterIdentity(IntegrationKind.EXECUTOR, "executor", "1", "cfg"),
            (DependencyObservation("runtime", True, "1"),),
            capabilities=("patch",), capability_digest="capability-digest",
            capability_provenance=CapabilityProvenance.DECLARED,
        )
        decision = plan.validate_capabilities(preflight)
        self.assertFalse(decision.allowed)

    def test_execution_plan_rejects_preflight_from_another_executor(self):
        plan = ExecutionPlan("plan-id", "task", "rev", "A", "executor", None, None, "sandbox", None, "cfg")
        preflight = assess_preflight(
            AdapterIdentity(IntegrationKind.EXECUTOR, "other", "1", "other-cfg"),
            (DependencyObservation("runtime", True, "1"),),
        )
        self.assertFalse(plan.preflight_matches_identity(preflight))

    def request(self):
        return ExecutionRequest("task", "rev", "A", "prompt", "executor", "provider", "model", "sandbox", "budget", "config")

    def test_fake_executor_is_replaceable_and_does_not_accept(self):
        result = ExecutionResult(RunState.COMPLETED, ("diff.patch",), output="done")
        executor = FakeExecutor(result)
        self.assertEqual(executor.execute(self.request()), result)
        self.assertEqual(len(executor.requests), 1)

    def test_failed_and_blocked_results_require_structured_error(self):
        error = ErrorEnvelope(ErrorDomain.PROVIDER, "UNAVAILABLE", "provider unavailable", Retryability.RETRYABLE)
        self.assertEqual(ExecutionResult(RunState.BLOCKED, error=error).error, error)
        with self.assertRaises(ValueError):
            ExecutionResult(RunState.FAILED)

    def test_provider_and_sandbox_are_independent_boundaries(self):
        provider = FakeProvider(ProviderResponse("answer", {"total_tokens": 3}))
        sandbox = FakeSandbox(("diff.patch",))
        provider.complete(ProviderRequest("prompt", "model", "config", "budget"))
        sandbox.prepare(SandboxRequest("task", "rev", "sandbox", "policy"))
        self.assertEqual(provider.response.output, "answer")
        self.assertEqual(sandbox.collect_artifacts(), ("diff.patch",))

    def test_provider_requires_versioned_configuration_bound_identity(self):
        provider = FakeProvider(ProviderResponse("answer"))
        self.assertEqual(validate_provider_identity(provider).name, "fake-provider")
        class AnonymousProvider:
            def complete(self, request):
                return ProviderResponse("answer")
        with self.assertRaises(ValueError):
            validate_provider_identity(AnonymousProvider())

    def test_sandbox_requires_versioned_configuration_bound_identity(self):
        sandbox = FakeSandbox()
        self.assertEqual(validate_sandbox_identity(sandbox).name, "fake-sandbox")
        class AnonymousSandbox:
            def prepare(self, request):
                return None
            def collect_artifacts(self):
                return ()
        with self.assertRaises(ValueError):
            validate_sandbox_identity(AnonymousSandbox())

    def test_unknown_provider_identity_is_preserved(self):
        request = self.request()
        value = ExecutionRequest(request.task_id, request.task_revision, request.treatment, request.prompt, request.executor_id, None, None, request.sandbox_id, request.budget_digest, request.configuration_digest)
        self.assertIsNone(value.provider_id)
        self.assertIsNone(value.model_id)

    def test_execution_plan_is_serializable_and_separate_from_result(self):
        plan = ExecutionPlan("plan-1", "task", "rev", "A", "executor", "provider", "model", "sandbox", "budget", "config", ("prepare", "execute"))
        request = plan.to_request("prompt")
        self.assertEqual(request.task_id, plan.task_id)
        self.assertEqual(plan.to_json(), plan.to_json())
        self.assertNotIn("state", plan.to_dict())

    def test_execution_plan_requires_identity(self):
        with self.assertRaises(ValueError):
            ExecutionPlan("", "task", None, "A", "executor", None, None, None, None, None)

    def test_execution_plan_binds_budget_digest(self):
        budget = ExecutionBudgetSpec(max_attempts=2, max_tokens=10)
        plan = ExecutionPlan("plan-1", "task", None, "A", "executor", None, None, None, None, None, (), budget)
        self.assertEqual(plan.budget_digest, budget.digest())
        with self.assertRaises(ValueError):
            ExecutionPlan("plan-2", "task", None, "A", "executor", None, None, None, "wrong", None, (), budget)

    def test_execution_plan_binds_configuration_snapshot_digest(self):
        snapshot = ConfigurationSnapshot("executor", "1.0", {"mode": "strict"})
        plan = ExecutionPlan("plan-config", "task", None, "A", "executor", None, None, None, None, None, (), configuration_snapshot=snapshot)
        self.assertEqual(plan.configuration_digest, snapshot.digest())
        with self.assertRaises(ValueError):
            ExecutionPlan("plan-config-bad", "task", None, "A", "executor", None, None, None, None, "other", (), configuration_snapshot=snapshot)

    def test_execution_plan_binds_provider_and_sandbox_identities(self):
        provider = AdapterIdentity(IntegrationKind.PROVIDER, "provider-a", "1", "provider-config")
        sandbox = AdapterIdentity(IntegrationKind.SANDBOX, "sandbox-a", "1", "sandbox-config")
        plan = ExecutionPlan("plan-integrations", "task", None, "A", "executor", "provider-a", None, "sandbox-a", None, None, (), provider_identity=provider, sandbox_identity=sandbox)
        self.assertEqual(plan.to_dict()["provider_identity"]["name"], "provider-a")
        with self.assertRaises(ValueError):
            ExecutionPlan("plan-bad-provider", "task", None, "A", "executor", "other", None, None, None, None, (), provider_identity=provider)

    def test_execution_chain_references_bind_plan_and_attempt(self):
        plan = ExecutionPlan("plan-1", "task", None, "A", "executor", None, None, None, None, None)
        validate_execution_chain(plan, plan_reference=plan.reference, execution_ref="execution://attempt-1", attempt_id="attempt-1")
        with self.assertRaises(ValueError):
            validate_execution_chain(plan, plan_reference="plan://other", execution_ref="execution://attempt-1", attempt_id="attempt-1")

    def test_public_execution_result_is_the_neutral_contract(self):
        import arkx
        from arkx.execution import ExecutionResult as NeutralExecutionResult
        from arkx.orchestration import ExecutionResult as LegacyExecutionResult
        self.assertIs(arkx.ExecutionResult, NeutralExecutionResult)
        self.assertIs(arkx.OrchestrationExecutionResult, LegacyExecutionResult)
        self.assertIsNot(arkx.ExecutionResult, arkx.OrchestrationExecutionResult)


if __name__ == "__main__":
    unittest.main()
