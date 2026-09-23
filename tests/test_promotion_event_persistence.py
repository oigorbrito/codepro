import tempfile
import unittest
from pathlib import Path

from arkx.acceptance import AcceptancePolicy, decide_independent_acceptance
from arkx.contracts import EventType
from arkx.event_log import EventLog, append_promotion_decision, replay_chain
from arkx.outcomes import VerificationResult, VerificationState
from arkx.promotion import PromotionCandidate, PromotionPolicy, decide_outcome_promotion


class PromotionEventPersistenceTests(unittest.TestCase):
    def test_promotion_is_persisted_only_after_acceptance(self):
        verification = VerificationResult(VerificationState.PASS, "verifier", ("pytest",), ("0",), ("evidence://verification",))
        acceptance = decide_independent_acceptance(verification, AcceptancePolicy("authority"))
        decision = decide_outcome_promotion(
            PromotionCandidate("executor", "candidate", "1", "cfg"), verification, acceptance,
            ("experiment://1",), PromotionPolicy("authority"),
        )
        with tempfile.TemporaryDirectory() as directory:
            log = EventLog(Path(directory) / "events.jsonl", run_id="run-1")
            log.append_stage(timestamp="2026-01-01T00:00:00+00:00", event_type=EventType.EVIDENCE_ADDED, stage="verification", ref=verification.reference)
            log.append_stage(timestamp="2026-01-01T00:00:01+00:00", event_type=EventType.EVIDENCE_ADDED, stage="acceptance", ref=acceptance.reference)
            self.assertTrue(append_promotion_decision(log, decision, verification_ref=verification.reference, timestamp="2026-01-01T00:00:02+00:00"))
            self.assertEqual(replay_chain(log.read(), run_id="run-1").promotion_ref, decision.reference)

    def test_promotion_rejects_acceptance_from_another_chain(self):
        verification = VerificationResult(VerificationState.PASS, "verifier", ("pytest",), ("0",), ("evidence://verification",))
        acceptance = decide_independent_acceptance(verification, AcceptancePolicy("authority"))
        decision = decide_outcome_promotion(PromotionCandidate("executor", "candidate", "1", "cfg"), verification, acceptance, ("experiment://1",), PromotionPolicy("authority"))
        with tempfile.TemporaryDirectory() as directory:
            log = EventLog(Path(directory) / "events.jsonl", run_id="run-1")
            log.append_stage(timestamp="2026-01-01T00:00:00+00:00", event_type=EventType.EVIDENCE_ADDED, stage="verification", ref=verification.reference)
            with self.assertRaises(ValueError):
                append_promotion_decision(log, decision, verification_ref=verification.reference, timestamp="2026-01-01T00:00:01+00:00")


if __name__ == "__main__":
    unittest.main()
