import unittest

from arkx.handoff import HandoffBudgetStatus, HandoffSummary
from arkx.characterization import RecommendedPath
from arkx.progress import ProgressSnapshot, assess_progress
from arkx.recovery import RecoveryAction, RecoveryReason, RecoveryRequest, decide_recovery
from arkx.routing import EvidenceSufficiency


def snapshots(*, progress=True):
    previous = ProgressSnapshot(
        useful_files=("a.py",), passing_tests=(), explained_failures=(), diff_distance=2,
        acceptance_distance=1, recent_actions=("inspect",), failure_signatures=("x",),
    )
    current = ProgressSnapshot(
        useful_files=("a.py",), passing_tests=("test_a",) if progress else (),
        explained_failures=(), diff_distance=1 if progress else 2,
        acceptance_distance=0 if progress else 1,
        recent_actions=("patch",) if progress else ("inspect",),
        failure_signatures=() if progress else ("x",),
    )
    return assess_progress(previous, current)


def handoff_summary(status=HandoffBudgetStatus.WITHIN_BUDGET):
    return HandoffSummary(1, (("executor-a", "executor-b"),), 10, 12, 0, 0, 0, 0, status)


class RecoveryControllerTests(unittest.TestCase):
    def test_progress_continues_without_selecting_executor(self):
        result = decide_recovery(
            current_path=RecommendedPath.LOCALIZED_PATH,
            progress=snapshots(),
            evidence=EvidenceSufficiency.SUFFICIENT,
        )
        self.assertEqual(result.action, RecoveryAction.CONTINUE)
        self.assertIsNone(result.target_executor_ref)

    def test_no_progress_escalates_with_budget(self):
        result = decide_recovery(
            current_path=RecommendedPath.SIMPLE_PATH,
            progress=snapshots(progress=False),
            evidence=EvidenceSufficiency.INSUFFICIENT,
        )
        self.assertEqual(result.action, RecoveryAction.ESCALATE)
        self.assertEqual(result.target_path, RecommendedPath.LOCALIZED_PATH)

    def test_replan_requires_causal_references(self):
        result = decide_recovery(
            current_path=RecommendedPath.SIMPLE_PATH,
            progress=snapshots(progress=False),
            evidence=EvidenceSufficiency.INSUFFICIENT,
            request=RecoveryRequest(action=RecoveryAction.REPLAN),
        )
        self.assertEqual(result.action, RecoveryAction.BLOCK)
        self.assertEqual(result.reason, RecoveryReason.REPLAN_REFERENCE_REQUIRED)

    def test_handoff_requires_explicit_identity_evidence_and_budget(self):
        result = decide_recovery(
            current_path=RecommendedPath.LOCALIZED_PATH,
            progress=snapshots(),
            evidence=EvidenceSufficiency.SUFFICIENT,
            request=RecoveryRequest(action=RecoveryAction.HANDOFF, target_executor_ref="executor-b"),
            handoff=handoff_summary(),
        )
        self.assertEqual(result.action, RecoveryAction.BLOCK)
        self.assertEqual(result.reason, RecoveryReason.HANDOFF_EVIDENCE_REQUIRED)

    def test_handoff_budget_exhaustion_blocks(self):
        result = decide_recovery(
            current_path=RecommendedPath.LOCALIZED_PATH,
            progress=snapshots(),
            evidence=EvidenceSufficiency.SUFFICIENT,
            request=RecoveryRequest(action=RecoveryAction.HANDOFF, target_executor_ref="executor-b", evidence_refs=("evidence://handoff",)),
            handoff=handoff_summary(HandoffBudgetStatus.BUDGET_EXCEEDED),
        )
        self.assertEqual(result.action, RecoveryAction.BLOCK)
        self.assertEqual(result.reason, RecoveryReason.HANDOFF_BUDGET_EXCEEDED)

    def test_explicit_handoff_is_allowed_only_with_all_bindings(self):
        result = decide_recovery(
            current_path=RecommendedPath.LOCALIZED_PATH,
            progress=snapshots(),
            evidence=EvidenceSufficiency.SUFFICIENT,
            request=RecoveryRequest(action=RecoveryAction.HANDOFF, target_executor_ref="executor-b", evidence_refs=("evidence://handoff",)),
            handoff=handoff_summary(),
        )
        self.assertEqual(result.action, RecoveryAction.HANDOFF)
        self.assertEqual(result.target_executor_ref, "executor-b")


if __name__ == "__main__":
    unittest.main()
