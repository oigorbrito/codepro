import json
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

from arkx.swebench_authority import (
    AUTHORITY_IDENTITY, OfficialEvaluationResult, OfficialEvaluationStatus,
    SWEbenchOfficialAuthority, SWEbenchPrediction, SWEbenchRecord,
    _evaluation_result_from_report, derive_harness_instance,
    derive_harness_instance_from_task_repo,
)
from arkx.submission import SubmissionArtifact

_SWEBENCH_AVAILABLE = importlib.util.find_spec("swebench") is not None
requires_swebench = unittest.skipUnless(
    _SWEBENCH_AVAILABLE,
    "BLOCKED: optional swebench package is unavailable; authority integration not executed",
)


def record():
    return SWEbenchRecord(
        "owner__repo-1", "owner/repo", "base", "problem", "1.0", "env",
        ("fail",), ("pass",), "test patch", "gold patch", "revision", "now",
    )


def raw_harness_record():
    return {
        "instance_id": "sympy__sympy-14711", "repo": "sympy/sympy", "version": "1.1",
        "FAIL_TO_PASS": ["test_Vector"], "PASS_TO_PASS": ["test_Vector_diffs"],
        "log_parser": "python", "eval_type": "FAIL_AND_PASS",
        "eval_script": "python -m pytest", "base_commit": "base",
    }


class SWEbenchAuthorityTests(unittest.TestCase):
    def test_prediction_serialization_has_no_gold_or_grading_labels(self):
        value = SWEbenchPrediction("task", "provider/model", "diff").to_dict()
        self.assertEqual(value, {"instance_id": "task", "model_name_or_path": "provider/model", "model_patch": "diff"})
        self.assertNotIn("gold_patch", value)

    def test_reference_prediction_uses_upstream_submission_byte_for_byte(self):
        submission = SubmissionArtifact.from_upstream_agent(
            "patch\r\n", attempt_id="attempt-1", executor_identity="mini-pinned"
        )
        value = SWEbenchPrediction.from_submission(
            instance_id="task", model_name_or_path="provider/model", submission=submission
        )
        self.assertEqual(value.model_patch, "patch\r\n")

    def test_reference_prediction_rejects_workspace_diff_source(self):
        submission = SubmissionArtifact(
            "workspace_diff", "diff", "diff", "hash", (), "raw", "normalized"
        )
        with self.assertRaisesRegex(ValueError, "upstream_agent submission"):
            SWEbenchPrediction.from_submission(
                instance_id="task", model_name_or_path="provider/model", submission=submission
            )

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

    def test_aggregate_report_distinguishes_empty_filter_from_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "provider-free.json"
            report.write_text(json.dumps({
                "submitted_ids": ["task"], "empty_patch_ids": ["task"],
                "resolved_ids": [], "unresolved_ids": [], "error_ids": [],
            }), encoding="utf-8")
            result = _evaluation_result_from_report(report_path=report, run_id="r", instance_id="task")
            self.assertEqual(result.status, OfficialEvaluationStatus.NOT_EXECUTED)
            self.assertEqual(result.raw_outcome, "EMPTY_PATCH_FILTERED")

    def test_aggregate_report_accepts_executed_unresolved_instance(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "provider-free.json"
            report.write_text(json.dumps({
                "submitted_ids": ["task"], "empty_patch_ids": [],
                "resolved_ids": [], "unresolved_ids": ["task"], "error_ids": [],
            }), encoding="utf-8")
            result = _evaluation_result_from_report(report_path=report, run_id="r", instance_id="task")
            self.assertEqual(result.status, OfficialEvaluationStatus.TESTS_FAILED)
            self.assertEqual(result.raw_outcome, "false")

    @requires_swebench
    def test_raw_record_is_explicitly_enriched_with_harness_image(self):
        raw = raw_harness_record()
        enriched = derive_harness_instance(
            raw, source_dataset_id="dataset", revision="rev", fingerprint="fp"
        )
        self.assertNotIn("image", raw)
        self.assertEqual(enriched.record["image"], "swebench/sweb.eval.x86_64.sympy_1776_sympy-14711:latest")
        self.assertEqual(enriched.source_dataset_id, "dataset")
        self.assertEqual(enriched.revision, "rev")
        self.assertEqual(enriched.fingerprint, "fp")
        self.assertEqual(enriched.instance_id, raw["instance_id"])
        self.assertTrue(enriched.raw_record_hash)
        self.assertIn("expected_image@5.0.2", enriched.derivation_authority)

    def test_missing_harness_field_is_blocked_without_a_default(self):
        raw = raw_harness_record()
        del raw["eval_script"]
        with self.assertRaisesRegex(ValueError, "eval_script"):
            derive_harness_instance(raw, source_dataset_id="dataset", revision="rev", fingerprint="fp")

    def test_each_required_derived_field_is_fail_closed(self):
        for field in ("log_parser", "eval_type", "eval_script"):
            with self.subTest(field=field):
                raw = raw_harness_record()
                del raw[field]
                with self.assertRaisesRegex(ValueError, field):
                    derive_harness_instance(raw, source_dataset_id="dataset", revision="rev", fingerprint="fp")

    @requires_swebench
    def test_wrong_image_identity_is_blocked(self):
        raw = raw_harness_record()
        raw["image"] = "wrong/image:latest"
        with self.assertRaisesRegex(ValueError, "wrong image identity"):
            derive_harness_instance(raw, source_dataset_id="dataset", revision="rev", fingerprint="fp")

    @requires_swebench
    def test_enriched_record_image_is_idempotently_verified(self):
        raw = raw_harness_record()
        raw["image"] = "swebench/sweb.eval.x86_64.sympy_1776_sympy-14711:latest"
        enriched = derive_harness_instance(raw, source_dataset_id="dataset", revision="rev", fingerprint="fp")
        self.assertEqual(enriched.derived_image, raw["image"])

    @requires_swebench
    def test_task_repo_is_the_authority_for_the_three_missing_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task = root / "tasks" / "sympy__sympy-14711"
            task.mkdir(parents=True)
            (root / "sweb.yaml").write_text(
                "datasets: [princeton-nlp/SWE-Bench_Verified]\nsplits: [test]\n"
            )
            (task / "task.yaml").write_text(
                "instance_id: sympy__sympy-14711\nrepo: sympy/sympy\n"
                "version: '1.1'\nbase_commit: base\nsplit: test\n"
                "datasets: [princeton-nlp/SWE-Bench_Verified]\n"
                "image: swebench/sweb.eval.x86_64.sympy_1776_sympy-14711:latest\n"
                "log_parser: python\neval_type: FAIL_AND_PASS\n"
            )
            (task / "tests.json").write_text(
                json.dumps({"FAIL_TO_PASS": ["test_Vector"], "PASS_TO_PASS": ["test_Vector_diffs"]})
            )
            (task / "eval.sh").write_text("#!/bin/bash\npytest\n")
            (task / "problem_statement.md").write_text("problem")
            (task / "gold.patch").write_text("diff --git a/a b/a\n")
            (task / "test.patch").write_text("diff --git a/t t\n")
            (task / "Dockerfile").write_text("FROM scratch\n")
            raw = raw_harness_record()
            raw.pop("log_parser")
            raw.pop("eval_type")
            raw.pop("eval_script")
            enriched = derive_harness_instance_from_task_repo(
                raw, task_repo=root, source_dataset_id="dataset", revision="rev", fingerprint="fp"
            )
            self.assertEqual(enriched.record["log_parser"], "python")
            self.assertEqual(enriched.record["eval_type"], "FAIL_AND_PASS")
            self.assertEqual(enriched.record["eval_script"].replace("\r\n", "\n"), "#!/bin/bash\npytest\n")
            raw_hash_source = raw_harness_record()
            for key in ("log_parser", "eval_type", "eval_script"):
                raw_hash_source.pop(key)
            expected_raw_hash = hashlib.sha256(
                json.dumps(raw_hash_source, sort_keys=True, ensure_ascii=False, default=str).encode()
            ).hexdigest()
            self.assertEqual(enriched.provenance()["raw_record_hash"], expected_raw_hash)
            self.assertEqual(enriched.provenance()["derived_fields"]["eval_script"]["derivation_authority"], "swebench.task.repo")

    @requires_swebench
    def test_make_test_spec_accepts_complete_derived_record(self):
        from swebench.harness.utils import make_test_spec
        enriched = derive_harness_instance(
            raw_harness_record(), source_dataset_id="dataset", revision="rev", fingerprint="fp"
        )
        spec = make_test_spec(enriched.to_dict())
        self.assertEqual(spec.image, "swebench/sweb.eval.x86_64.sympy_1776_sympy-14711:latest")

    @requires_swebench
    def test_unknown_task_repo_identity_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex((KeyError, ValueError, FileNotFoundError), "sympy__sympy-14711|identity|tasks"):
                derive_harness_instance_from_task_repo(
                    raw_harness_record(), task_repo=directory,
                    source_dataset_id="dataset", revision="rev", fingerprint="fp"
                )


if __name__ == "__main__":
    unittest.main()
