import unittest

from arkx.execution import ContractRun, ExecutionRequest, ExecutionResult, FakeExecutor
from arkx.harness import AcceptanceEvidence, ErrorDomain, ErrorEnvelope, Retryability, RunState, VerificationEvidence


class ContractLifecycleTests(unittest.TestCase):
    def request(self):
        return ExecutionRequest("task", "rev", "A", "prompt", "executor", "provider", "model", "sandbox", "budget", "config")

    def test_fake_flow_preserves_lifecycle_and_does_not_infer_acceptance(self):
        run = ContractRun.execute(self.request(), FakeExecutor(ExecutionResult(RunState.COMPLETED, ("diff",))))
        self.assertEqual(run.state_history, (RunState.PLANNED, RunState.STARTED, RunState.EXECUTING, RunState.COMPLETED))
        self.assertFalse(run.is_accepted())

    def test_verification_and_acceptance_are_attached_independently(self):
        run = ContractRun.execute(self.request(), FakeExecutor(ExecutionResult(RunState.COMPLETED, ("diff",))))
        run = run.with_verification(VerificationEvidence("verifier", "PASS", ("verification://1",)))
        self.assertFalse(run.is_accepted())
        run = run.with_acceptance(AcceptanceEvidence("acceptance", "ACCEPTED", ("acceptance://1",)))
        self.assertTrue(run.is_accepted())

    def test_blocked_flow_requires_error_and_is_never_accepted(self):
        error = ErrorEnvelope(ErrorDomain.SANDBOX, "UNAVAILABLE", "sandbox unavailable", Retryability.NOT_RETRYABLE)
        run = ContractRun.execute(self.request(), FakeExecutor(ExecutionResult(RunState.BLOCKED, error=error)))
        self.assertEqual(run.state_history[-1], RunState.BLOCKED)
        self.assertFalse(run.is_accepted())


if __name__ == "__main__":
    unittest.main()
