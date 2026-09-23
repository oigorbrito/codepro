import unittest

from arkx.handoff import HandoffRecord
from arkx.planning import ReplanRequest, ReplanTrigger
from arkx.progress import Confidence, ProgressAssessment, ProgressEvidence, ProgressStatus
from arkx.recovery import RecoveryAction, RecoveryReason, build_recovery_plan, decide_recovery, plan_recovery_attempt, validate_recovery_reference
from arkx.routing import EscalationAction, EscalationDecision, EvidenceSufficiency, RecommendedPath
from arkx.harness import derive_attempt_id


def progress(status):
    return ProgressAssessment(1, status, Confidence.HIGH, (), (), None, {}, ProgressEvidence((), (), (), None, None, None, None))


def escalation(action, current=RecommendedPath.LOCALIZED_PATH, target=RecommendedPath.REPOSITORY_WIDE_PATH):
    return EscalationDecision(1, current, action, target, (), progress(ProgressStatus.NO_PROGRESS).status, EvidenceSufficiency.INSUFFICIENT, None)  # type: ignore[arg-type]


class RecoveryTests(unittest.TestCase):
    def test_authorized_path_escalation_is_explicit(self):
        result = decide_recovery(escalation(EscalationAction.ESCALATE), progress(ProgressStatus.NO_PROGRESS))
        self.assertEqual(result.action, RecoveryAction.ESCALATE)
        self.assertIn(RecoveryReason.PATH_ESCALATION_AUTHORIZED, result.reason_codes)

    def test_no_progress_can_replan_when_escalation_is_not_available(self):
        request = ReplanRequest(ReplanTrigger.BLOCKED_STEP, "plan-1", ("evidence://stagnation",), 100)
        result = decide_recovery(escalation(EscalationAction.CONTINUE), progress(ProgressStatus.NO_PROGRESS), replan_request=request)
        self.assertEqual(result.action, RecoveryAction.REPLAN)
        self.assertEqual(result.replan_request.previous_plan_ref, "plan-1")

    def test_unknown_requires_qualification(self):
        result = decide_recovery(escalation(EscalationAction.REQUIRE_QUALIFICATION), progress(ProgressStatus.UNKNOWN))
        self.assertEqual(result.action, RecoveryAction.BLOCK)
        self.assertIn(RecoveryReason.QUALIFICATION_REQUIRED, result.reason_codes)

    def test_handoff_requires_reason_and_evidence(self):
        record = HandoffRecord("h-1", "a", "b", None, (), "summary", 1, 1, 0, 0, 0, ())
        result = decide_recovery(escalation(EscalationAction.CONTINUE), progress(ProgressStatus.PROGRESS_PROVEN), handoffs=(record,))
        self.assertEqual(result.action, RecoveryAction.BLOCK)
        self.assertIn(RecoveryReason.HANDOFF_EVIDENCE_MISSING, result.reason_codes)

    def test_exhausted_replan_budget_blocks(self):
        request = ReplanRequest(ReplanTrigger.BLOCKED_STEP, "plan-1", ("evidence://stagnation",), 100)
        result = decide_recovery(escalation(EscalationAction.CONTINUE), progress(ProgressStatus.NO_PROGRESS), replans_used=1, replan_request=request)
        self.assertEqual(result.action, RecoveryAction.BLOCK)

    def test_recovery_plan_binds_decision_to_source_attempt_deterministically(self):
        decision = decide_recovery(escalation(EscalationAction.ESCALATE), progress(ProgressStatus.NO_PROGRESS))
        first = build_recovery_plan("attempt-1", decision)
        second = build_recovery_plan("attempt-1", decision)
        self.assertEqual(first.to_json(), second.to_json())
        self.assertEqual(first.source_attempt_id, "attempt-1")
        validate_recovery_reference(first, first.reference)
        with self.assertRaises(ValueError):
            validate_recovery_reference(first, "recovery://other")

    def test_recovery_attempt_plan_derives_a_new_identity(self):
        source = derive_attempt_id(trial_id="trial", attempt_number=1, configuration_digest="cfg")
        plan = plan_recovery_attempt(trial_id="trial", source_attempt_id=source, source_attempt_number=1, configuration_digest="cfg", recovery_reference="recovery://1")
        self.assertNotEqual(plan.next_attempt_id, plan.source_attempt_id)
        self.assertEqual(plan.next_attempt_number, 2)
        with self.assertRaises(ValueError):
            plan_recovery_attempt(trial_id="trial", source_attempt_id="wrong", source_attempt_number=1, configuration_digest="cfg", recovery_reference="recovery://1")


if __name__ == "__main__":
    unittest.main()
