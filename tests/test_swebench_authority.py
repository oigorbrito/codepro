import json
import tempfile
import unittest
from pathlib import Path

from arkx.swebench_authority import (
    AUTHORITY_IDENTITY, OfficialEvaluationResult, OfficialEvaluationStatus,
    SWEbenchOfficialAuthority, SWEbenchPrediction, SWEbenchRecord,
)


def record():
    return SWEbenchRecord(
        "owner__repo-1", "owner/repo", "base", "problem", "1.0", "env",
        ("fail",), ("pass",), "test patch", "gold patch", "revision", "now",
    )


class SWEbenchAuthorityTests(unittest.TestCase):
    def test_prediction_serialization_has_no_gold_or_grading_labels(self):
        value = SWEbenchPrediction("task", "provider/model", "diff").to_dict()
        self.assertEqual(value, {"instance_id": "task", "model_name_or_path": "provider/model", "model_patch": "diff"})
        self.assertNotIn("gold_patch", value)

    def test_executor_payload_excludes_gold_and_test_labels(self):
        value = record().executor_payload()
        self.assertNotIn("gold_patch", value)
        self.assertNotIn("FAIL_TO_PASS", value)
        self.assertNotIn("test_patch", value)

    def test_official_outcome_mapping(self):
        accepted = OfficialEvaluationResult(OfficialEvaluationStatus.RESOLVED, AUTHORITY_IDENTITY, "r1", "t", "resolved", "report", ())
        rejected = OfficialEvaluationResult(OfficialEvaluationStatus.TESTS_FAILED, AUTHORITY_IDENTITY, "r2", "t", "failed", "report", ())
        infra = OfficialEvaluationResult(OfficialEvaluationStatus.INFRASTRUCTURE_ERROR, AUTHORITY_IDENTITY, "r3", "t", None, None, ())
        self.assertEqual(accepted.acceptance().decision.value, "ACCEPTED")
        self.assertEqual(rejected.acceptance().decision.value, "REJECTED")
        self.assertEqual(infra.acceptance().decision.value, "INDETERMINATE")

    def test_evaluator_infrastructure_failure_is_not_a_test_failure(self):
        infra = OfficialEvaluationResult(
            OfficialEvaluationStatus.INFRASTRUCTURE_ERROR,
            AUTHORITY_IDENTITY,
            "r3",
            "t",
            None,
            "report",
            ("log",),
            "docker daemon unavailable",
        )
        rejected = OfficialEvaluationResult(
            OfficialEvaluationStatus.TESTS_FAILED,
            AUTHORITY_IDENTITY,
            "r4",
            "t",
            "failed",
            "report",
            (),
        )
        error = infra.error_envelope()
        self.assertEqual(error.domain.value, "VERIFICATION")
        self.assertEqual(error.code, "EVALUATOR_INFRASTRUCTURE_ERROR")
        self.assertEqual(error.retryability.value, "UNKNOWN")
        self.assertEqual(error.raw_evidence_refs, ("log", "report"))
        self.assertIsNone(rejected.error_envelope())

    def test_evaluator_maps_to_verification_without_acceptance_or_promotion(self):
        result = OfficialEvaluationResult(
            OfficialEvaluationStatus.TESTS_FAILED,
            AUTHORITY_IDENTITY,
            "r5",
            "t",
            "failed",
            "report",
            ("log",),
        )
        verification = result.verification_result()
        self.assertEqual(verification.state.value, "FAIL")
        self.assertEqual(verification.authority, AUTHORITY_IDENTITY)
        self.assertEqual(verification.commands, ("swebench.harness.run_evaluation",))
        self.assertEqual(verification.evidence, ("log", "report"))
        self.assertTrue(verification.reference.startswith("verification://"))
        self.assertEqual(result.acceptance().decision.value, "REJECTED")

    def test_authority_persists_prediction_and_raw_artifact_link(self):
        with tempfile.TemporaryDirectory() as directory:
            def evaluator(payload):
                prediction = json.loads(Path(payload["predictions_path"]).read_text(encoding="utf-8"))
                self.assertEqual(prediction["instance_id"], "owner__repo-1")
                return OfficialEvaluationResult(OfficialEvaluationStatus.RESOLVED, AUTHORITY_IDENTITY, payload["run_id"], "owner__repo-1", "resolved", payload["predictions_path"], ())
            result = SWEbenchOfficialAuthority(directory, evaluator).evaluate(record=record(), model_name_or_path="m", model_patch="diff", run_id="unique-run")
            self.assertEqual(result.status, OfficialEvaluationStatus.RESOLVED)
            self.assertTrue(Path(result.report_path).exists())

    def test_same_run_id_is_not_reused_for_a_second_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            authority = SWEbenchOfficialAuthority(directory, lambda payload: OfficialEvaluationResult(OfficialEvaluationStatus.RESOLVED, AUTHORITY_IDENTITY, payload["run_id"], "owner__repo-1", "resolved", None, ()))
            authority.evaluate(record=record(), model_name_or_path="m", model_patch="one", run_id="r")
            blocked = authority.evaluate(record=record(), model_name_or_path="m", model_patch="two", run_id="r")
            self.assertEqual(blocked.status, OfficialEvaluationStatus.BLOCKED)


if __name__ == "__main__":
    unittest.main()
