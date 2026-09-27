import itertools
import unittest
from dataclasses import replace

from arkx.characterization import RecommendedPath
from arkx.progress import ProgressSnapshot, ProgressStatus, assess_progress
from arkx.promotion import (
    CriterionOperator,
    GateStatus,
    PromotionCriterion,
    PromotionGate,
    assess_promotion_gate,
    freeze_promotion_gate,
)
from arkx.routing import (
    EscalationAction,
    EvidenceSufficiency,
    assess_escalation,
)
from arkx.verification import (
    PatchVerificationInput,
    PatchVerificationStatus,
    TestResult,
    TestResultStatus,
    verify_patch,
)


class RoutingPropertyTests(unittest.TestCase):
    def test_stop_requires_proven_progress_and_sufficient_evidence(self):
        previous = ProgressSnapshot(
            useful_files=("src/a.py",),
            passing_tests=(),
            explained_failures=(),
            diff_distance=2,
            acceptance_distance=1,
            recent_actions=("inspect",),
            failure_signatures=("failure-a",),
        )
        current = replace(previous, passing_tests=("test_a",), acceptance_distance=0)
        base = assess_progress(previous, current)

        paths = (
            RecommendedPath.SIMPLE_PATH,
            RecommendedPath.LOCALIZED_PATH,
            RecommendedPath.REPOSITORY_WIDE_PATH,
        )
        for path, status, evidence in itertools.product(
            paths,
            tuple(ProgressStatus),
            tuple(EvidenceSufficiency),
        ):
            progress = replace(base, status=status)
            decision = assess_escalation(path, progress, evidence)
            if decision.action is EscalationAction.STOP_SUFFICIENT_EVIDENCE:
                self.assertEqual(status, ProgressStatus.PROGRESS_PROVEN)
                self.assertEqual(evidence, EvidenceSufficiency.SUFFICIENT)
            if status is ProgressStatus.PROGRESS_PROVEN and evidence is EvidenceSufficiency.SUFFICIENT:
                self.assertEqual(decision.action, EscalationAction.STOP_SUFFICIENT_EVIDENCE)


class VerificationPropertyTests(unittest.TestCase):
    def test_verified_is_equivalent_to_all_required_gates(self):
        regression_modes = {
            "missing": None,
            "empty": (),
            "failed": (
                TestResult("required", TestResultStatus.FAILED, True, "evidence://test"),
            ),
            "not_executed": (
                TestResult("required", TestResultStatus.NOT_EXECUTED, True, None),
            ),
            "passed_without_evidence": (
                TestResult("required", TestResultStatus.PASSED, True, None),
            ),
            "passed": (
                TestResult("required", TestResultStatus.PASSED, True, "evidence://test"),
            ),
        }
        scope_modes = {
            "missing": (None, ("src/a.py",)),
            "unchanged": (("src/a.py",), ("src/a.py",)),
            "expanded": (("src/a.py", "src/b.py"), ("src/a.py",)),
        }
        evidence_modes = {
            "missing": None,
            "empty": (),
            "blank": ("   ",),
            "valid": ("evidence://patch",),
        }

        for (
            reproduced_before,
            reproduces_after,
            patch_applied,
            regression_name,
            scope_name,
            evidence_name,
        ) in itertools.product(
            (None, False, True),
            (None, False, True),
            (None, False, True),
            tuple(regression_modes),
            tuple(scope_modes),
            tuple(evidence_modes),
        ):
            changed_files, expected_scope = scope_modes[scope_name]
            result = verify_patch(
                PatchVerificationInput(
                    task_id="property-task",
                    issue_reproduction_required=True,
                    issue_reproduced_before_patch=reproduced_before,
                    patch_applied=patch_applied,
                    regression_results=regression_modes[regression_name],
                    issue_reproduces_after_patch=reproduces_after,
                    changed_files=changed_files,
                    expected_scope=expected_scope,
                    evidence_refs=evidence_modes[evidence_name],
                )
            )
            all_required_gates = (
                reproduced_before is True
                and reproduces_after is False
                and patch_applied is True
                and regression_name == "passed"
                and scope_name == "unchanged"
                and evidence_name == "valid"
            )
            self.assertEqual(
                result.status is PatchVerificationStatus.VERIFIED,
                all_required_gates,
                msg=(
                    reproduced_before,
                    reproduces_after,
                    patch_applied,
                    regression_name,
                    scope_name,
                    evidence_name,
                    result.status,
                ),
            )


class PromotionPropertyTests(unittest.TestCase):
    def test_eligibility_requires_every_criterion_and_every_evidence_key(self):
        gate = freeze_promotion_gate(
            PromotionGate(
                gate_id="property-gate",
                criteria=(
                    PromotionCriterion(
                        "resolution",
                        "resolution_delta",
                        CriterionOperator.GTE,
                        0.0,
                        "resolution must not degrade",
                    ),
                    PromotionCriterion(
                        "cost",
                        "cost_ratio",
                        CriterionOperator.LTE,
                        1.0,
                        "cost must not increase",
                    ),
                ),
                required_evidence_keys=("analysis", "validity", "raw_runs"),
            )
        )

        for resolution, cost, mask in itertools.product(
            (None, -0.1, 0.0, 0.1),
            (None, 0.8, 1.0, 1.2),
            itertools.product((False, True), repeat=3),
        ):
            keys = ("analysis", "validity", "raw_runs")
            evidence = {
                key: f"evidence://{key}"
                for key, present in zip(keys, mask)
                if present
            }
            assessment = assess_promotion_gate(
                gate,
                {"resolution_delta": resolution, "cost_ratio": cost},
                evidence,
            )
            all_criteria = (
                isinstance(resolution, (int, float))
                and resolution >= 0.0
                and isinstance(cost, (int, float))
                and cost <= 1.0
            )
            all_evidence = all(mask)
            self.assertEqual(
                assessment.status is GateStatus.ELIGIBLE_FOR_REVIEW,
                all_criteria and all_evidence,
                msg=(resolution, cost, mask, assessment.status),
            )


if __name__ == "__main__":
    unittest.main()
