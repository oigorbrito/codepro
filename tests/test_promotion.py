import unittest

from arkx.p82_baseline import AcceptanceDecision, AcceptanceResult
from arkx.harness import VerificationEvidence
from arkx.harness import AttemptSnapshot, RunManifest, RunState
from arkx.promotion import (
    PromotionCandidate,
    PromotionPolicy,
    PromotionReason,
    PromotionStatus,
    decide_snapshot_promotion,
    decide_promotion,
    decide_outcome_promotion,
    load_promotion_decision,
    write_promotion_decision,
)
from arkx.outcomes import VerificationResult, VerificationState


def candidate(**overrides):
    values = {"component_type": "executor", "component_id": "mini", "version": "1.0", "configuration_digest": "digest"}
    values.update(overrides)
    return PromotionCandidate(**values)


def accepted(**overrides):
    values = {"decision": AcceptanceDecision.ACCEPTED, "authority": "authority-1", "raw_outcome": "accepted", "evidence": ("evidence://acceptance",)}
    values.update(overrides)
    return AcceptanceResult(**values)


def verified(**overrides):
    values = {"authority_identity": "verifier-1", "state": "PASS", "evidence_refs": ("evidence://verification",)}
    values.update(overrides)
    return VerificationEvidence(**values)


class PromotionTests(unittest.TestCase):
    def test_accepted_candidate_with_evidence_is_promoted(self):
        result = decide_promotion(candidate(), accepted(), ("experiment://p8.3/trial-1",), PromotionPolicy("authority-1"), verified())
        self.assertEqual(result.status, PromotionStatus.PROMOTED)
        self.assertIn(PromotionReason.PROMOTED_WITH_INDEPENDENT_EVIDENCE, result.reason_codes)

    def test_missing_acceptance_is_blocked(self):
        result = decide_promotion(candidate(), None, ("experiment://1",), PromotionPolicy("authority-1"), verified())
        self.assertEqual(result.status, PromotionStatus.BLOCKED)
        self.assertIn(PromotionReason.ACCEPTANCE_REQUIRED, result.reason_codes)

    def test_missing_evidence_is_blocked(self):
        result = decide_promotion(candidate(), accepted(), (), PromotionPolicy("authority-1"), verified())
        self.assertEqual(result.status, PromotionStatus.BLOCKED)
        self.assertIn(PromotionReason.EVIDENCE_MISSING, result.reason_codes)

    def test_authority_mismatch_is_blocked(self):
        result = decide_promotion(candidate(), accepted(authority="other"), ("experiment://1",), PromotionPolicy("authority-1"), verified())
        self.assertEqual(result.status, PromotionStatus.BLOCKED)

    def test_indeterminate_acceptance_is_not_promoted(self):
        result = decide_promotion(candidate(), accepted(decision=AcceptanceDecision.INDETERMINATE), ("experiment://1",), PromotionPolicy("authority-1"), verified())
        self.assertEqual(result.status, PromotionStatus.INDETERMINATE)

    def test_rejected_acceptance_is_not_promoted(self):
        result = decide_promotion(candidate(), accepted(decision=AcceptanceDecision.REJECTED), ("experiment://1",), PromotionPolicy("authority-1"), verified())
        self.assertEqual(result.status, PromotionStatus.NOT_PROMOTED)

    def test_serialization_is_deterministic(self):
        first = decide_promotion(candidate(), accepted(), ("b", "a"), PromotionPolicy("authority-1"), verified()).to_json()
        second = decide_promotion(candidate(), accepted(), ("a", "b"), PromotionPolicy("authority-1"), verified()).to_json()
        self.assertEqual(first, second)

    def test_verification_is_required_for_promotion(self):
        result = decide_promotion(candidate(), accepted(), ("experiment://1",), PromotionPolicy("authority-1"))
        self.assertEqual(result.status, PromotionStatus.BLOCKED)
        self.assertIn(PromotionReason.VERIFICATION_REQUIRED, result.reason_codes)

    def test_verification_without_evidence_is_blocked(self):
        result = decide_promotion(candidate(), accepted(), ("experiment://1",), PromotionPolicy("authority-1"), verified(evidence_refs=()))
        self.assertEqual(result.status, PromotionStatus.BLOCKED)
        self.assertIn(PromotionReason.VERIFICATION_EVIDENCE_MISSING, result.reason_codes)

    def test_snapshot_promotion_requires_completed_matching_attempt(self):
        manifest = RunManifest(
            experiment_id="exp", trial_id="trial", attempt_id="attempt", attempt_number=1,
            task_id="task", task_revision="rev", treatment="A", executor="executor",
            provider="provider", model="model", sandbox="sandbox", repository_revision="rev",
            configuration_digest="digest", protocol_version="protocol", state=RunState.BLOCKED,
        )
        snapshot = AttemptSnapshot(manifest, {}, ())
        result = decide_snapshot_promotion(candidate(), snapshot, accepted(), ("evidence://1",), PromotionPolicy("authority-1"), verified())
        self.assertEqual(result.status, PromotionStatus.BLOCKED)
        self.assertIn(PromotionReason.EXECUTION_NOT_COMPLETED, result.reason_codes)

    def test_snapshot_promotion_binds_decision_to_attempt_and_verification_refs(self):
        manifest = RunManifest(
            experiment_id="exp", trial_id="trial", attempt_id="attempt", attempt_number=1,
            task_id="task", task_revision="rev", treatment="A", executor="executor",
            provider="provider", model="model", sandbox="sandbox", repository_revision="rev",
            configuration_digest="digest", protocol_version="protocol", state=RunState.COMPLETED,
        )
        snapshot = AttemptSnapshot(manifest, {}, ())
        result = decide_snapshot_promotion(candidate(configuration_digest="digest"), snapshot, accepted(), ("evidence://promotion",), PromotionPolicy("authority-1"), verified())
        self.assertEqual(result.status, PromotionStatus.PROMOTED)
        self.assertEqual(result.attempt_id, "attempt")
        self.assertTrue(result.reference.startswith("promotion://"))
        self.assertIn("evidence://verification", result.evidence_refs)

    def test_promotion_decision_persistence_is_immutable_and_bound(self):
        import tempfile
        from pathlib import Path
        manifest = RunManifest(
            experiment_id="exp", trial_id="trial", attempt_id="attempt", attempt_number=1,
            task_id="task", task_revision="rev", treatment="A", executor="executor",
            provider="provider", model="model", sandbox="sandbox", repository_revision="rev",
            configuration_digest="digest", protocol_version="protocol", state=RunState.COMPLETED,
        )
        snapshot = AttemptSnapshot(manifest, {}, ())
        decision = decide_snapshot_promotion(candidate(configuration_digest="digest"), snapshot, accepted(), ("evidence://promotion",), PromotionPolicy("authority-1"), verified())
        with tempfile.TemporaryDirectory() as directory:
            path = write_promotion_decision(decision, Path(directory) / "promotion.json")
            restored = load_promotion_decision(path, snapshot)
            self.assertEqual(restored.attempt_id, "attempt")
            with self.assertRaises(FileExistsError):
                write_promotion_decision(decision, path)

    def test_outcome_promotion_requires_acceptance_to_reference_verification(self):
        verification = VerificationResult(VerificationState.PASS, "verifier", ("pytest",), ("0",), ("evidence://verification",))
        acceptance = AcceptanceResult(AcceptanceDecision.ACCEPTED, "authority-1", "accepted", ("evidence://acceptance",))
        blocked = decide_outcome_promotion(candidate(), verification, acceptance, ("experiment://1",), PromotionPolicy("authority-1"))
        self.assertEqual(blocked.status, PromotionStatus.BLOCKED)
        self.assertIn(PromotionReason.ACCEPTANCE_VERIFICATION_MISMATCH, blocked.reason_codes)

        accepted_result = AcceptanceResult(
            AcceptanceDecision.ACCEPTED,
            "authority-1",
            "accepted",
            tuple(sorted((verification.reference, "evidence://verification"))),
        )
        promoted = decide_outcome_promotion(candidate(), verification, accepted_result, ("experiment://1",), PromotionPolicy("authority-1"))
        self.assertEqual(promoted.status, PromotionStatus.PROMOTED)


if __name__ == "__main__":
    unittest.main()
