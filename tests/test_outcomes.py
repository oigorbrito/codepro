import unittest

from arkx.outcomes import (
    AcceptanceDecision,
    AcceptanceResult,
    VerificationResult,
    VerificationState,
    validate_outcome_references,
)


class OutcomeContractTests(unittest.TestCase):
    def test_serialization_is_executor_neutral(self):
        verification = VerificationResult(
            VerificationState.PASS,
            "verifier-v1",
            ("pytest",),
            ("passed",),
            ("evidence://verification/1",),
        )
        acceptance = AcceptanceResult(
            AcceptanceDecision.ACCEPTED,
            "authority-v1",
            "verified",
            ("evidence://acceptance/1",),
        )
        self.assertEqual(verification.to_dict(), {
            "state": "PASS",
            "authority": "verifier-v1",
            "commands": ["pytest"],
            "outcomes": ["passed"],
            "evidence": ["evidence://verification/1"],
        })
        self.assertEqual(acceptance.to_dict(), {
            "decision": "ACCEPTED",
            "authority": "authority-v1",
            "raw_outcome": "verified",
            "evidence": ["evidence://acceptance/1"],
        })

    def test_references_are_deterministic_and_validated(self):
        verification = VerificationResult(
            VerificationState.PASS,
            "verifier-1",
            ("pytest",),
            ("PASS",),
            ("artifact://v",),
        )
        acceptance = AcceptanceResult(
            AcceptanceDecision.ACCEPTED,
            "authority-1",
            "accepted",
            ("acceptance://evidence",),
        )
        self.assertEqual(verification.reference, verification.reference)
        self.assertNotEqual(verification.reference, acceptance.reference)
        validate_outcome_references(
            verification,
            acceptance,
            verification_ref=verification.reference,
            acceptance_ref=acceptance.reference,
        )
        with self.assertRaises(ValueError):
            validate_outcome_references(
                verification,
                acceptance,
                verification_ref="verification://wrong",
                acceptance_ref=acceptance.reference,
            )


if __name__ == "__main__":
    unittest.main()
