import unittest

from arkx.contracts import Event, EventType
from arkx.event_log import EventLog, ReplayChain, ReplayState, ResumeAction, append_recovery_plan, decide_resume, replay_chain, validate_attempt_lineage_chain
from arkx.harness import AttemptSnapshot, RecoveryLineage, RunManifest, RunState, derive_attempt_id
from arkx.recovery import RecoveryAction, RecoveryDecision, RecoveryReason, build_recovery_plan
from arkx.characterization import RecommendedPath


class ReplayChainTests(unittest.TestCase):
    def test_attempt_lineage_requires_matching_event_references(self):
        attempt_id = derive_attempt_id(trial_id="trial-1", attempt_number=2, configuration_digest="cfg")
        source_id = derive_attempt_id(trial_id="trial-1", attempt_number=1, configuration_digest="cfg")
        manifest = RunManifest("exp", "trial-1", attempt_id, 2, "task", "rev", "A", "executor", "provider", "model", "sandbox", "repo", "cfg", "protocol", budget_ledger={"consumed_attempts": [source_id, attempt_id]})
        snapshot = AttemptSnapshot(manifest, {}, (), recovery_lineage=RecoveryLineage("trial-1", source_id, 1, attempt_id, 2, "cfg", "recovery://2"))
        replay = ReplayState(attempt_id, 2, budget_ledger=manifest.budget_ledger, recovery_source_attempt_id=source_id)
        validate_attempt_lineage_chain(snapshot, ReplayChain(execution_ref=f"execution://{attempt_id}", recovery_ref="recovery://2"), replay)
        with self.assertRaises(ValueError):
            validate_attempt_lineage_chain(snapshot, ReplayChain(execution_ref=f"execution://{attempt_id}"), replay)
    def test_resume_decision_only_returns_safe_persisted_boundary(self):
        self.assertEqual(decide_resume(replay_chain((Event("2026-01-01T00:00:00+00:00", EventType.EVIDENCE_ADDED, "run-1", {"stage": "plan", "ref": "plan://1"}),), run_id="run-1"), ReplayState("run-1", 1)).action, ResumeAction.RESTART_REQUIRED)
        execution = replay_chain((Event("2026-01-01T00:00:00+00:00", EventType.EVIDENCE_ADDED, "run-1", {"stage": "execution", "ref": "execution://1"}),), run_id="run-1")
        self.assertEqual(decide_resume(execution, ReplayState("run-1", 1)).action, ResumeAction.RESUME_VERIFICATION)
        verified = ReplayChain(execution_ref="execution://1", verification_ref="verification://1")
        self.assertEqual(decide_resume(verified, ReplayState("run-1", 2)).action, ResumeAction.RESUME_ACCEPTANCE)
        terminal = ReplayState("run-1", 1, declared_status="ACCEPTED")
        self.assertEqual(decide_resume(verified, terminal).action, ResumeAction.TERMINAL)
    def test_recovery_persistence_requires_matching_execution(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as directory:
            log = EventLog(Path(directory) / "events.jsonl", run_id="attempt-1")
            log.append_stage(timestamp="2026-01-01T00:00:00+00:00", event_type=EventType.EVIDENCE_ADDED, stage="execution", ref="execution://attempt-1")
            decision = RecoveryDecision(RecoveryAction.REPLAN, (RecoveryReason.NO_PROGRESS_REQUIRES_REPLAN,), RecommendedPath.SIMPLE_PATH, RecommendedPath.LOCALIZED_PATH)
            plan = build_recovery_plan("attempt-1", decision)
            self.assertTrue(append_recovery_plan(log, plan, "execution://attempt-1", "2026-01-01T00:00:01+00:00"))
            with self.assertRaises(ValueError):
                append_recovery_plan(log, plan, "execution://other", "2026-01-01T00:00:02+00:00")
    def test_replay_chain_reconstructs_explicit_stage_references(self):
        events = tuple(
            Event(f"2026-01-01T00:00:0{index}+00:00", EventType.EVIDENCE_ADDED, "run-1", {"stage": stage, "ref": f"{stage}://1"})
            for index, stage in enumerate(("request", "plan", "execution", "recovery", "verification", "acceptance", "promotion"))
        )
        chain = replay_chain(events, run_id="run-1")
        self.assertEqual(chain.promotion_ref, "promotion://1")
        self.assertIsNotNone(chain.verification_ref)

    def test_recovery_reference_is_optional_but_ordered(self):
        events = (
            Event("2026-01-01T00:00:00+00:00", EventType.EVIDENCE_ADDED, "run-1", {"stage": "execution", "ref": "execution://1"}),
            Event("2026-01-01T00:00:01+00:00", EventType.REPLAN, "run-1", {"stage": "recovery", "ref": "recovery://1"}),
            Event("2026-01-01T00:00:02+00:00", EventType.EVIDENCE_ADDED, "run-1", {"stage": "verification", "ref": "verification://1"}),
        )
        chain = replay_chain(events, run_id="run-1")
        self.assertEqual(chain.recovery_ref, "recovery://1")

    def test_replay_chain_rejects_out_of_order_stages(self):
        events = (
            Event("2026-01-01T00:00:00+00:00", EventType.EVIDENCE_ADDED, "run-1", {"stage": "execution", "ref": "execution://1"}),
            Event("2026-01-01T00:00:01+00:00", EventType.EVIDENCE_ADDED, "run-1", {"stage": "plan", "ref": "plan://1"}),
        )
        with self.assertRaises(ValueError):
            replay_chain(events, run_id="run-1")

    def test_replay_chain_rejects_stage_reference_drift(self):
        events = (
            Event("2026-01-01T00:00:00+00:00", EventType.EVIDENCE_ADDED, "run-1", {"stage": "verification", "ref": "verification://1"}),
            Event("2026-01-01T00:00:01+00:00", EventType.EVIDENCE_ADDED, "run-1", {"stage": "verification", "ref": "verification://2"}),
        )
        with self.assertRaises(ValueError):
            replay_chain(events, run_id="run-1")


if __name__ == "__main__":
    unittest.main()
