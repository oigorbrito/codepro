from __future__ import annotations

import importlib.util
import inspect
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "tools" / "run_mini_v246_gemini_api_qualification.py"

spec = importlib.util.spec_from_file_location("mini_v246_gemini_api_qualification", RUNNER_PATH)
assert spec is not None and spec.loader is not None
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class MiniV246GeminiApiQualificationTests(unittest.TestCase):
    def test_frozen_mini_identity(self) -> None:
        self.assertEqual(runner.MINI_VERSION, "v2.4.6")
        self.assertEqual(
            runner.MINI_SHA,
            "a83fcae82d2a08f0ee0c688f9d137b3566c097f8",
        )
        self.assertEqual(
            runner.MINI_CONFIG_BLOB,
            "106decd160e72e5164e29d15d23da354c29c309d",
        )

    def test_provider_model_identity(self) -> None:
        self.assertEqual(runner.MODEL, "gemini/gemini-2.5-flash")
        self.assertEqual(runner.PROVIDER_CREDENTIAL_ENV, "GEMINI_API_KEY")

    def test_provider_free_gate_requires_complete_block5_evidence(self) -> None:
        valid = {
            "classification": "MINI_V246_PROVIDER_FREE_RUNTIME_QUALIFIED",
            "controls": {
                "no_op": {
                    "execution": "PASS",
                    "verification": "EXPECTED_FAIL",
                    "cleanup": "PASS",
                },
                "gold_oracle": {
                    "execution": "PASS",
                    "verification": "PASS",
                    "cleanup": "PASS",
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "runner-summary.json"
            path.write_text(json.dumps(valid), encoding="utf-8")
            self.assertTrue(runner.provider_free_gate_ok(path))

            for mutation in (
                lambda d: d.__setitem__("classification", "OTHER"),
                lambda d: d["controls"]["no_op"].__setitem__("verification", "PASS"),
                lambda d: d["controls"]["gold_oracle"].__setitem__("verification", "FAIL"),
                lambda d: d["controls"]["gold_oracle"].__setitem__("cleanup", "FAIL"),
            ):
                candidate = json.loads(json.dumps(valid))
                mutation(candidate)
                path.write_text(json.dumps(candidate), encoding="utf-8")
                self.assertFalse(runner.provider_free_gate_ok(path))

    def test_verifier_identity_reuses_block5_builder_and_exact_pins(self) -> None:
        source = inspect.getsource(runner.ensure_verifier_image)
        self.assertIn("_load_verifier_builder()", source)
        self.assertIn("_verifier_image_identity_command()", source)
        self.assertIn("_DOCKERFILE", source)
        self.assertEqual(runner.VERIFIER_IMAGE, "codepro/swebench-verifier:5.0.2")
        self.assertEqual(runner.SWEBENCH_VERSION, "5.0.2")
        self.assertEqual(
            runner.TASK_REPO_COMMIT,
            "3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d",
        )

    def test_prediction_record_requires_target_instance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "preds.json"
            path.write_text(
                json.dumps(
                    {
                        "sympy__sympy-14711": {
                            "instance_id": "sympy__sympy-14711",
                            "model_patch": "diff --git a/a b/a\n",
                        }
                    }
                ),
                encoding="utf-8",
            )
            record = runner.prediction_record(path, "sympy__sympy-14711")
            self.assertIsNotNone(record)
            self.assertTrue(record["model_patch"].strip())
            self.assertIsNone(runner.prediction_record(path, "other__task-1"))

    def test_main_requires_trajectory_and_nonempty_patch(self) -> None:
        source = inspect.getsource(runner.main)
        self.assertIn("trajectory_present = traj_path.exists()", source)
        self.assertIn("patch_present = isinstance(patch, str) and bool(patch.strip())", source)
        self.assertIn("not trajectory_present or not patch_present", source)
        self.assertIn('"reason"] = "EXECUTOR_RUN_NOT_OBSERVABLE"', source)

    def test_verifier_outcomes_distinguish_definitive_from_ambiguous(self) -> None:
        instance = "sympy__sympy-14711"
        cases = (
            ({"resolved_ids": [instance]}, "RESOLVED"),
            ({"unresolved_ids": [instance]}, "TESTS_FAILED"),
            ({"infra_failure_ids": [instance]}, "INFRASTRUCTURE_ERROR"),
            ({"ambiguous_failure_ids": [instance]}, "AMBIGUOUS"),
            ({}, "AMBIGUOUS"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            for payload, expected in cases:
                path.write_text(json.dumps(payload), encoding="utf-8")
                self.assertEqual(runner.verifier_outcome(path, instance), expected)

        self.assertIn("RESOLVED", {"RESOLVED", "TESTS_FAILED"})
        self.assertIn("TESTS_FAILED", {"RESOLVED", "TESTS_FAILED"})
        self.assertNotIn("INFRASTRUCTURE_ERROR", {"RESOLVED", "TESTS_FAILED"})
        self.assertNotIn("AMBIGUOUS", {"RESOLVED", "TESTS_FAILED"})

    def test_qualification_does_not_authorize_product_binding_or_promotion(self) -> None:
        source = RUNNER_PATH.read_text(encoding="utf-8")
        self.assertIn('"executor_promotion": "NOT_AUTHORIZED"', source)
        self.assertIn('"product_binding": "NOT_AUTHORIZED"', source)
        self.assertIn('"treatment": {', source)
        self.assertIn('"name": "mini-v246-gemini-api"', source)
        self.assertNotIn("gemini-cli", source.lower())
        self.assertNotIn("fallback", source.lower().replace("no fallback", ""))


if __name__ == "__main__":
    unittest.main()
