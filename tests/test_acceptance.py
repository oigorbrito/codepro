import unittest

from arkx.acceptance import AcceptancePolicy, decide_independent_acceptance
from arkx.p82_baseline import AcceptanceDecision, VerificationResult, VerificationState


class AcceptanceTests(unittest.TestCase):
    def test_verified_with_evidence_is_accepted_by_explicit_authority(self):
        result = decide_independent_acceptance(VerificationResult(VerificationState.PASS, "verifier", ("pytest",), ("0",), ("evidence://log",)), AcceptancePolicy("authority"))
        self.assertEqual(result.decision, AcceptanceDecision.ACCEPTED)
        self.assertEqual(result.authority, "authority")
        self.assertTrue(any(item.startswith("verification://") for item in result.evidence))

    def test_verified_without_evidence_is_blocked(self):
        result = decide_independent_acceptance(VerificationResult(VerificationState.PASS, "verifier", (), (), ()), AcceptancePolicy("authority"))
        self.assertEqual(result.decision, AcceptanceDecision.BLOCKED)

    def test_unknown_verification_is_not_accepted(self):
        result = decide_independent_acceptance(VerificationResult(VerificationState.INDETERMINATE, "verifier", (), (), ("evidence://unknown",)), AcceptancePolicy("authority"))
        self.assertEqual(result.decision, AcceptanceDecision.INDETERMINATE)

    def test_missing_verification_authority_is_blocked(self):
        result = decide_independent_acceptance(VerificationResult(VerificationState.PASS, "", (), (), ("evidence://log",)), AcceptancePolicy("authority"))
        self.assertEqual(result.decision, AcceptanceDecision.BLOCKED)


if __name__ == "__main__":
    unittest.main()
