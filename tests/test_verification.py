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
        "reproduction_before": True,
        "patch_applied": True,
        "regression_results": (TestResult("regression", TestResultStatus.PASSED, True, "e://test"),),
        "reproduction_after": False,
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
        self.assertNotIn("PASS", result.to_json())

    def test_required_reproduction_absent_is_blocked(self):
        result = verify_patch(valid(reproduction_before=None))
        self.assertEqual(result.status, PatchVerificationStatus.BLOCKED)
        self.assertIn(ReasonCode.REPRODUCTION_REQUIRED_MISSING, result.reason_codes)

    def test_regression_failure_is_rejected(self):
        result = verify_patch(valid(regression_results=(TestResult("regression", TestResultStatus.FAILED, True),)))
        self.assertEqual(result.status, PatchVerificationStatus.REJECTED)

    def test_post_patch_reproduction_failure_is_rejected(self):
        result = verify_patch(valid(reproduction_after=True))
        self.assertEqual(result.status, PatchVerificationStatus.REJECTED)

    def test_scope_expansion_is_rejected(self):
        result = verify_patch(valid(changed_files=("src/a.py", "src/unexpected.py")))
        self.assertEqual(result.status, PatchVerificationStatus.REJECTED)
        self.assertTrue(result.scope_changed)

    def test_incomplete_evidence_is_unknown(self):
        result = verify_patch(valid(patch_applied=None))
        self.assertEqual(result.status, PatchVerificationStatus.UNKNOWN)

    def test_required_not_executed_is_not_passed(self):
        result = verify_patch(valid(regression_results=(TestResult("regression", TestResultStatus.NOT_EXECUTED, True),)))
        self.assertEqual(result.status, PatchVerificationStatus.BLOCKED)
        self.assertIsNone(result.regression_tests_passed)

    def test_missing_evidence_is_blocked(self):
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

