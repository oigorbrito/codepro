import json
import unittest
from pathlib import Path

from arkx.verification import (
    PatchVerificationInput,
    PatchVerificationStatus,
    ReasonCode,
    TestResult,
    TestResultStatus,
    verify_patch,
)


def valid(**overrides):
    values = {
        "task_id": "task",
        "issue_reproduction_required": True,
        "issue_reproduced_before_patch": True,
        "patch_applied": True,
        "regression_results": (
            TestResult("regression", TestResultStatus.PASSED, True, "e://test"),
        ),
        "issue_reproduces_after_patch": False,
        "changed_files": ("src/a.py",),
        "expected_scope": ("src/a.py",),
        "evidence_refs": ("e://patch",),
    }
    values.update(overrides)
    return PatchVerificationInput(**values)


class VerificationTests(unittest.TestCase):
    def test_all_gates_produce_verified_not_pass(self):
        result = verify_patch(valid())
        self.assertEqual(result.status, PatchVerificationStatus.VERIFIED)
        self.assertTrue(result.issue_reproduced_before_patch)
        self.assertFalse(result.issue_reproduces_after_patch)
        self.assertNotIn("PASS", result.to_json())

    def test_schema_v2_uses_unambiguous_reproduction_fields(self):
        payload = verify_patch(valid()).to_dict()
        self.assertEqual(payload["schema_version"], 2)
        self.assertIn("issue_reproduced_before_patch", payload)
        self.assertIn("issue_reproduces_after_patch", payload)
        self.assertNotIn("reproduction_passed_after_patch", payload)
        self.assertNotIn("reproduces_issue", payload)

    def test_required_reproduction_absent_before_patch_is_blocked(self):
        result = verify_patch(valid(issue_reproduced_before_patch=None))
        self.assertEqual(result.status, PatchVerificationStatus.BLOCKED)
        self.assertIn(
            ReasonCode.REPRODUCTION_REQUIRED_MISSING_BEFORE_PATCH,
            result.reason_codes,
        )

    def test_required_reproduction_absent_after_patch_is_blocked(self):
        result = verify_patch(valid(issue_reproduces_after_patch=None))
        self.assertEqual(result.status, PatchVerificationStatus.BLOCKED)
        self.assertIn(
            ReasonCode.REPRODUCTION_REQUIRED_MISSING_AFTER_PATCH,
            result.reason_codes,
        )

    def test_issue_must_reproduce_before_patch(self):
        result = verify_patch(valid(issue_reproduced_before_patch=False))
        self.assertEqual(result.status, PatchVerificationStatus.REJECTED)
        self.assertIn(ReasonCode.ISSUE_NOT_REPRODUCED_BEFORE_PATCH, result.reason_codes)

    def test_regression_failure_is_rejected(self):
        result = verify_patch(
            valid(
                regression_results=(
                    TestResult("regression", TestResultStatus.FAILED, True),
                )
            )
        )
        self.assertEqual(result.status, PatchVerificationStatus.REJECTED)

    def test_issue_still_reproducing_after_patch_is_rejected(self):
        result = verify_patch(valid(issue_reproduces_after_patch=True))
        self.assertEqual(result.status, PatchVerificationStatus.REJECTED)
        self.assertIn(ReasonCode.ISSUE_STILL_REPRODUCES_AFTER_PATCH, result.reason_codes)

    def test_reproduction_gate_can_be_not_applicable(self):
        result = verify_patch(
            valid(
                issue_reproduction_required=False,
                issue_reproduced_before_patch=None,
                issue_reproduces_after_patch=None,
            )
        )
        self.assertEqual(result.status, PatchVerificationStatus.VERIFIED)

    def test_scope_expansion_is_rejected(self):
        result = verify_patch(valid(changed_files=("src/a.py", "src/unexpected.py")))
        self.assertEqual(result.status, PatchVerificationStatus.REJECTED)
        self.assertTrue(result.scope_changed)

    def test_incomplete_patch_evidence_is_unknown(self):
        result = verify_patch(valid(patch_applied=None))
        self.assertEqual(result.status, PatchVerificationStatus.UNKNOWN)

    def test_required_not_executed_is_not_passed(self):
        result = verify_patch(
            valid(
                regression_results=(
                    TestResult("regression", TestResultStatus.NOT_EXECUTED, True),
                )
            )
        )
        self.assertEqual(result.status, PatchVerificationStatus.BLOCKED)
        self.assertIsNone(result.regression_tests_passed)

    def test_missing_evidence_refs_is_blocked(self):
        result = verify_patch(valid(evidence_refs=()))
        self.assertEqual(result.status, PatchVerificationStatus.BLOCKED)
        self.assertFalse(result.evidence_sufficient)

    def test_fixture_is_classified_as_verification_fixture(self):
        path = Path(__file__).parents[1] / "experiments" / "patch-verification-fixture.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(value["fixture_type"], "PATCH_VERIFICATION_FIXTURE")
        self.assertEqual(len(value["scenarios"]), 6)


if __name__ == "__main__":
    unittest.main()
