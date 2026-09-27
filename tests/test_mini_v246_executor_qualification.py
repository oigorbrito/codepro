from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "run_mini_v246_executor_qualification.py"
SPEC = importlib.util.spec_from_file_location("mini_v246_executor_qualification", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class MiniV246ExecutorQualificationTests(unittest.TestCase):
    def test_frozen_identity_matches_phase1_reference(self) -> None:
        self.assertEqual(runner.MINI_VERSION, "v2.4.6")
        self.assertEqual(runner.MINI_SHA, "a83fcae82d2a08f0ee0c688f9d137b3566c097f8")
        self.assertEqual(runner.MINI_CONFIG_BLOB, "106decd160e72e5164e29d15d23da354c29c309d")
        self.assertEqual(runner.MODEL, "anthropic/claude-sonnet-4-5-20250929")
        self.assertEqual(runner.COST_LIMIT_USD, 3)
        self.assertEqual(runner.WORKERS, 1)
        self.assertEqual(runner.ENVIRONMENT_CLASS, "docker")

    def test_provider_free_gate_requires_both_controls_and_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.json"
            path.write_text(
                json.dumps(
                    {
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
                ),
                encoding="utf-8",
            )
            self.assertTrue(runner.provider_free_gate_ok(path))
            data = json.loads(path.read_text(encoding="utf-8"))
            data["controls"]["gold_oracle"]["cleanup"] = "FAIL"
            path.write_text(json.dumps(data), encoding="utf-8")
            self.assertFalse(runner.provider_free_gate_ok(path))

    def test_definitive_verifier_outcomes_do_not_rank_patch_quality(self) -> None:
        for key, expected in (("resolved_ids", "RESOLVED"), ("unresolved_ids", "TESTS_FAILED")):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "report.json"
                path.write_text(json.dumps({key: ["sympy__sympy-14711"]}), encoding="utf-8")
                self.assertEqual(runner.verifier_outcome(path, "sympy__sympy-14711"), expected)

    def test_infrastructure_and_ambiguous_reports_are_not_definitive(self) -> None:
        cases = (
            ({"infra_failure_ids": ["sympy__sympy-14711"]}, "INFRASTRUCTURE_ERROR"),
            ({"error_ids": ["sympy__sympy-14711"]}, "INFRASTRUCTURE_ERROR"),
            ({"ambiguous_failure_ids": ["sympy__sympy-14711"]}, "AMBIGUOUS"),
        )
        for payload, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "report.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                self.assertEqual(runner.verifier_outcome(path, "sympy__sympy-14711"), expected)

    def test_prediction_record_accepts_upstream_dict_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "preds.json"
            path.write_text(
                json.dumps(
                    {
                        "sympy__sympy-14711": {
                            "instance_id": "sympy__sympy-14711",
                            "model_name_or_path": runner.MODEL,
                            "model_patch": "diff --git a/a.py b/a.py\n",
                        }
                    }
                ),
                encoding="utf-8",
            )
            pred = runner.prediction_record(path, "sympy__sympy-14711")
            self.assertIsNotNone(pred)
            self.assertTrue(pred["model_patch"].startswith("diff --git"))

    def test_verifier_helper_uses_official_task_identity(self) -> None:
        self.assertIn('load_task_repo("/opt/swe-bench-tasks"', runner._VERIFIER_HELPER)
        self.assertIn("task identity mismatch", runner._VERIFIER_HELPER)
        self.assertIn("swebench.harness.run_evaluation", runner._VERIFIER_HELPER)


if __name__ == "__main__":
    unittest.main()
