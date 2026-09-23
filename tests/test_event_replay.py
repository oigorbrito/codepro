import unittest

from arkx.contracts import Event, EventType
from arkx.event_log import replay_events, validate_replay_against_manifest, validate_replay_outcomes, validate_replay_telemetry
from arkx.harness import AcceptanceEvidence, RunManifest, RunState, VerificationEvidence, derive_attempt_id


class EventReplayTests(unittest.TestCase):
    def test_replay_restores_budget_ledger_and_rejects_drift(self):
        ledger = {"budget_digest": "b", "consumed_attempts": ["attempt"]}
        event = Event("2026-01-01T00:00:00+00:00", EventType.EVIDENCE_ADDED, "run-1", {"budget_ledger": ledger})
        replay = replay_events((event,), run_id="run-1")
        self.assertEqual(replay.budget_ledger, ledger)
        drift = Event("2026-01-01T00:00:01+00:00", EventType.EVIDENCE_ADDED, "run-1", {"budget_ledger": {"budget_digest": "other"}})
        with self.assertRaises(ValueError):
            replay_events((event, drift), run_id="run-1")
    def test_replay_reconstructs_declared_facts_without_execution(self):
        events = (
            Event("2026-01-01T00:00:00+00:00", EventType.TASK_STARTED, "run-1"),
            Event("2026-01-01T00:00:01+00:00", EventType.EXECUTOR_STARTED, "run-1"),
            Event("2026-01-01T00:00:02+00:00", EventType.RETRY, "run-1"),
            Event("2026-01-01T00:00:03+00:00", EventType.EVIDENCE_ADDED, "run-1", {"ref": "artifact://1"}),
            Event("2026-01-01T00:00:04+00:00", EventType.TASK_FINISHED, "run-1", {"status": "BLOCKED"}),
        )
        state = replay_events(events, run_id="run-1")
        self.assertEqual((state.event_count, state.executor_invocations, state.retry_count), (5, 1, 1))
        self.assertEqual(state.declared_status, "BLOCKED")
        self.assertEqual(state.evidence_refs, ("artifact://1",))

    def test_replay_rejects_wrong_run_id(self):
        with self.assertRaises(ValueError):
            replay_events((Event("2026-01-01T00:00:00+00:00", EventType.TASK_STARTED, "other"),), run_id="run-1")

    def test_replay_manifest_consistency_is_validated(self):
        trial_id = "trial-task-treatment-1"
        manifest = RunManifest(
            experiment_id="exp-1", trial_id=trial_id,
            attempt_id=derive_attempt_id(trial_id=trial_id, attempt_number=1, configuration_digest="cfg-a"),
            attempt_number=1, task_id="task-1", task_revision="task-rev-1", treatment="A",
            executor="executor-x", provider="provider-x", model="model-x", sandbox="sandbox-x",
            repository_revision="repo-rev-1", configuration_digest="cfg-a", protocol_version="protocol-1",
            state=RunState.BLOCKED,
        )
        replay = replay_events((Event("2026-01-01T00:00:00+00:00", EventType.TASK_FINISHED, manifest.attempt_id, {"status": "BLOCKED"}),), run_id=manifest.attempt_id)
        validate_replay_against_manifest(manifest, replay)
        inconsistent = replay_events((Event("2026-01-01T00:00:00+00:00", EventType.TASK_FINISHED, manifest.attempt_id, {"status": "COMPLETED"}),), run_id=manifest.attempt_id)
        with self.assertRaises(ValueError):
            validate_replay_against_manifest(manifest, inconsistent)

    def test_replay_keeps_verification_and_acceptance_separate(self):
        events = (
            Event("2026-01-01T00:00:00+00:00", EventType.EVIDENCE_ADDED, "run-1", {"verification_state": "PASS", "acceptance_decision": "REJECTED"}),
        )
        replay = replay_events(events, run_id="run-1")
        self.assertEqual((replay.verification_state, replay.acceptance_decision), ("PASS", "REJECTED"))
        validate_replay_outcomes(replay, verification=VerificationEvidence("v", "PASS"), acceptance=AcceptanceEvidence("a", "REJECTED"))
        with self.assertRaises(ValueError):
            validate_replay_outcomes(replay, acceptance=AcceptanceEvidence("a", "ACCEPTED"))

    def test_replay_reconstructs_operational_outcome_fields(self):
        event = Event(
            "2026-01-01T00:00:00+00:00",
            EventType.EVIDENCE_ADDED,
            "run-1",
            {"stage": "execution", "ref": "execution://1", "execution_outcome": "BLOCKED", "error_code": "SANDBOX_PROCESS_126"},
        )
        replay = replay_events((event,), run_id="run-1")
        self.assertEqual(replay.execution_outcome, "BLOCKED")
        self.assertEqual(replay.error_codes, ("SANDBOX_PROCESS_126",))

    def test_replay_telemetry_rejects_verification_drift(self):
        event = Event("2026-01-01T00:00:00+00:00", EventType.EVIDENCE_ADDED, "run-1", {"verification_state": "PASS"})
        replay = replay_events((event,), run_id="run-1")
        from arkx.outcomes import VerificationResult, VerificationState
        with self.assertRaises(ValueError):
            validate_replay_telemetry(replay, verification=VerificationResult(VerificationState.FAIL, "v", (), (), ("e",)))


if __name__ == "__main__":
    unittest.main()
