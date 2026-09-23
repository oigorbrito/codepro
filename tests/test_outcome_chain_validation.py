import unittest

from arkx.acceptance import AcceptancePolicy, decide_independent_acceptance
from arkx.event_log import ReplayChain, validate_outcome_chain
from arkx.outcomes import VerificationResult, VerificationState
from arkx.promotion import PromotionCandidate, PromotionPolicy, decide_outcome_promotion


class OutcomeChainValidationTests(unittest.TestCase):
    def _objects(self):
        verification = VerificationResult(
            VerificationState.PASS,
            "verifier",
            ("pytest",),
            ("0",),
            ("evidence://verification",),
        )
        acceptance = decide_independent_acceptance(verification, AcceptancePolicy("authority"))
        promotion = decide_outcome_promotion(
            PromotionCandidate("executor", "candidate", "1", "cfg"),
            verification,
            acceptance,
            ("experiment://1",),
            PromotionPolicy("authority"),
        )
        return verification, acceptance, promotion

    def test_replay_chain_must_match_all_outcome_objects(self):
        verification, acceptance, promotion = self._objects()
        chain = ReplayChain(
            verification_ref=verification.reference,
            acceptance_ref=acceptance.reference,
            promotion_ref=promotion.reference,
        )
        validate_outcome_chain(chain, verification=verification, acceptance=acceptance, promotion=promotion)

    def test_replay_chain_rejects_object_reference_drift(self):
        verification, acceptance, promotion = self._objects()
        chain = ReplayChain(
            verification_ref="verification://different",
            acceptance_ref=acceptance.reference,
            promotion_ref=promotion.reference,
        )
        with self.assertRaises(ValueError):
            validate_outcome_chain(chain, verification=verification, acceptance=acceptance, promotion=promotion)


if __name__ == "__main__":
    unittest.main()
