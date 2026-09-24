import unittest

from arkx.acceptance import AcceptanceAuthority, AcceptanceReason, AcceptanceStatus, decide_acceptance
from arkx.spine import SpineStatus, execute_governed, verify_observation
from tests.test_spine import FixtureExecutor, current_progress, execute_fixture, grant, previous_progress, request, signals, verification


def accepted_record():
    record, _ = execute_fixture()
    return verify_observation(record, previous_progress(), current_progress(), verification())


def authority(*, independent=True, ref="acceptance://reviewer"):
    return AcceptanceAuthority(ref, independent, "evidence://authority-identity")


class IndependentAcceptanceTests(unittest.TestCase):
    def test_accepts_verified_execution_with_independent_authority(self):
        decision = decide_acceptance(
            accepted_record(), authority(), run_id="run://fixture-1",
            execution_artifact_ref="artifact://execution-1", verification_ref="artifact://verification-1",
            evidence_refs=("evidence://authority-identity", "evidence://verification"),
            rationale="verified reproduction and regression evidence",
        )
        self.assertEqual(decision.status, AcceptanceStatus.ACCEPTED)
        self.assertEqual(decision.reason, AcceptanceReason.VERIFIED)
        self.assertEqual(decision.run_id, "run://fixture-1")

    def test_blocks_non_independent_authority_and_missing_evidence(self):
        record = accepted_record()
        not_independent = decide_acceptance(
            record, authority(independent=False), run_id="run://fixture-2",
            execution_artifact_ref="artifact://execution-2", verification_ref="artifact://verification-2",
            evidence_refs=("evidence://verification",), rationale="executor cannot accept its own result",
        )
        no_evidence = decide_acceptance(
            record, authority(), run_id="run://fixture-3",
            execution_artifact_ref="artifact://execution-3", verification_ref="artifact://verification-3",
            evidence_refs=(), rationale="missing evidence",
        )
        self.assertEqual(not_independent.reason, AcceptanceReason.AUTHORITY_NOT_INDEPENDENT)
        self.assertEqual(no_evidence.reason, AcceptanceReason.EVIDENCE_REQUIRED)

    def test_preserves_rejected_and_blocked_boundaries(self):
        record, _ = execute_fixture(executor=FixtureExecutor())
        rejected_record = verify_observation(
            record, previous_progress(), current_progress(), verification(issue_reproduces_after_patch=True)
        )
        rejected = decide_acceptance(
            rejected_record, authority(), run_id="run://rejected",
            execution_artifact_ref="artifact://execution-r", verification_ref="artifact://verification-r",
            evidence_refs=("evidence://verification",), rationale="regression remains",
        )
        blocked_record = execute_governed(
            request(),
            grant(),
            signals(candidate_files=("src/outside.py",)),
            capability_id="repository-edit", runtimes=(), qualifications=(), executor=FixtureExecutor()
        )
        blocked = decide_acceptance(
            blocked_record, authority(), run_id="run://blocked", execution_artifact_ref=None, verification_ref=None,
            evidence_refs=("evidence://authority-identity",), rationale="governance did not permit execution",
        )
        self.assertEqual(rejected_record.status, SpineStatus.REJECTED)
        self.assertEqual(rejected.status, AcceptanceStatus.REJECTED)
        self.assertEqual(blocked.status, AcceptanceStatus.BLOCKED)
        self.assertEqual(blocked.reason, AcceptanceReason.EXECUTION_BLOCKED)

    def test_authority_binding_is_not_silently_replaced(self):
        decision = decide_acceptance(
            accepted_record(), authority(ref="acceptance://other"), run_id="run://mismatch",
            execution_artifact_ref="artifact://execution", verification_ref="artifact://verification",
            evidence_refs=("evidence://verification",), rationale="wrong authority reference",
        )
        self.assertEqual(decision.status, AcceptanceStatus.BLOCKED)
        self.assertEqual(decision.reason, AcceptanceReason.AUTHORITY_MISMATCH)


if __name__ == "__main__":
    unittest.main()
