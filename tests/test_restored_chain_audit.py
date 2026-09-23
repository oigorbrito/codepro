import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from arkx.acceptance import AcceptancePolicy, decide_independent_acceptance
from arkx.contracts import Event, EventType
from arkx.event_log import ChainIntegrity, EventLog, audit_restored_chain
from arkx.harness import AttemptSnapshot, AttemptStore, RunManifest, RunState, derive_attempt_id
from arkx.event_log import ResumeAction
from arkx.outcomes import VerificationResult, VerificationState
from arkx.promotion import PromotionCandidate, PromotionPolicy, decide_outcome_promotion


class RestoredChainAuditTests(unittest.TestCase):
    def test_restored_chain_audit_replays_without_execution(self):
        trial_id = "trial-1"
        attempt_id = derive_attempt_id(trial_id=trial_id, attempt_number=1, configuration_digest="cfg")
        manifest = RunManifest(
            experiment_id="exp", trial_id=trial_id, attempt_id=attempt_id, attempt_number=1,
            task_id="task", task_revision="rev", treatment="A", executor="executor",
            provider="provider", model="model", sandbox="sandbox", repository_revision="rev",
            configuration_digest="cfg", protocol_version="protocol", state=RunState.COMPLETED,
        )
        snapshot = AttemptSnapshot(manifest, {}, ())
        verification = VerificationResult(VerificationState.PASS, "verifier", ("pytest",), ("0",), ("evidence://v",))
        acceptance = decide_independent_acceptance(verification, AcceptancePolicy("authority"))
        promotion = decide_outcome_promotion(
            PromotionCandidate("executor", "candidate", "1", "cfg"), verification, acceptance,
            ("experiment://1",), PromotionPolicy("authority"),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            log = EventLog(path, run_id=attempt_id)
            for index, (stage, ref) in enumerate((
                ("verification", verification.reference),
                ("acceptance", acceptance.reference),
                ("promotion", promotion.reference),
            )):
                log.append(Event(f"2026-01-01T00:00:0{index}+00:00", EventType.EVIDENCE_ADDED, attempt_id, {"stage": stage, "ref": ref, "protocol_version": "protocol", "schema_version": 1, "configuration_digest": "cfg", "treatment": "A"}))
            audit = audit_restored_chain(path, snapshot, verification=verification, acceptance=acceptance, promotion=promotion, protocol_version="protocol")
        self.assertEqual(audit.integrity, ChainIntegrity.INCOMPLETE)
        self.assertEqual(audit.references.missing, ())
        self.assertEqual(audit.replay.event_count, 3)
        self.assertEqual(audit.resume_decision.action, ResumeAction.RESTART_REQUIRED)

    def test_restored_chain_rejects_protocol_drift(self):
        manifest = RunManifest(
            experiment_id="exp", trial_id="trial", attempt_id="attempt", attempt_number=1,
            task_id="task", task_revision="rev", treatment="A", executor="executor",
            provider="provider", model="model", sandbox="sandbox", repository_revision="rev",
            configuration_digest="cfg", protocol_version="protocol", state=RunState.COMPLETED,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            EventLog(path, run_id="attempt").append(Event("2026-01-01T00:00:00+00:00", EventType.EVIDENCE_ADDED, "attempt", {"stage": "verification", "ref": "verification://1", "protocol_version": "other", "schema_version": 1}))
            with self.assertRaises(ValueError):
                audit_restored_chain(path, AttemptSnapshot(manifest, {}, ()), protocol_version="protocol")

    def test_restored_chain_rejects_configuration_drift(self):
        manifest = RunManifest(
            experiment_id="exp", trial_id="trial", attempt_id="attempt", attempt_number=1,
            task_id="task", task_revision="rev", treatment="A", executor="executor",
            provider="provider", model="model", sandbox="sandbox", repository_revision="rev",
            configuration_digest="cfg", protocol_version="protocol", state=RunState.COMPLETED,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            EventLog(path, run_id="attempt").append(Event("2026-01-01T00:00:00+00:00", EventType.EVIDENCE_ADDED, "attempt", {"stage": "verification", "ref": "verification://1", "protocol_version": "protocol", "schema_version": 1, "configuration_digest": "other", "treatment": "A"}))
            with self.assertRaises(ValueError):
                audit_restored_chain(path, AttemptSnapshot(manifest, {}, ()), protocol_version="protocol", configuration_digest="cfg")

    def test_restored_chain_audit_rejects_manifest_status_divergence(self):
        manifest = RunManifest(
            experiment_id="exp", trial_id="trial", attempt_id="attempt", attempt_number=1,
            task_id="task", task_revision="rev", treatment="A", executor="executor",
            provider="provider", model="model", sandbox="sandbox", repository_revision="rev",
            configuration_digest="cfg", protocol_version="protocol", state=RunState.COMPLETED,
        )
        snapshot = AttemptSnapshot(manifest, {}, ())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            EventLog(path, run_id="attempt").append(Event("2026-01-01T00:00:00+00:00", EventType.TASK_FINISHED, "attempt", {"status": "BLOCKED"}))
            with self.assertRaises(ValueError):
                audit_restored_chain(path, snapshot)

    def test_attempt_store_exposes_audited_loading(self):
        snapshot = AttemptSnapshot(
            RunManifest(
                experiment_id="exp", trial_id="trial", attempt_id="attempt", attempt_number=1,
                task_id="task", task_revision="rev", treatment="A", executor="executor",
                provider="provider", model="model", sandbox="sandbox", repository_revision="rev",
                configuration_digest="cfg", protocol_version="protocol", state=RunState.COMPLETED,
            ),
            {},
            (),
        )
        with patch("arkx.harness.load_attempt", return_value=snapshot) as loader:
            with patch("arkx.event_log.audit_restored_chain", return_value="audited") as auditor:
                result = AttemptStore("artifacts").load_audited("attempt-root", "events.jsonl")
        self.assertEqual(result, "audited")
        loader.assert_called_once_with("attempt-root")
        auditor.assert_called_once_with("events.jsonl", snapshot)


if __name__ == "__main__":
    unittest.main()
