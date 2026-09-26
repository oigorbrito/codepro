from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "run_gemini_cli_executor_qualification.py"
SPEC = importlib.util.spec_from_file_location("gemini_cli_executor_qualification", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class GeminiCliExecutorQualificationTests(unittest.TestCase):
    def test_frozen_executor_identity(self) -> None:
        self.assertEqual(runner.GEMINI_EXECUTOR, "gemini-cli")
        self.assertEqual(runner.GEMINI_MODEL, "gemini-3-pro-preview")
        self.assertEqual(runner.GEMINI_APPROVAL_MODE, "yolo")
        self.assertEqual(runner.DEFAULT_INSTANCE, "sympy__sympy-14711")
        self.assertEqual(runner.SWEBENCH_VERSION, "5.0.2")

    def test_windows_cmd_shim_is_explicitly_invoked_through_comspec(self) -> None:
        argv = runner.tool_argv(
            r"C:\\Users\\me\\AppData\\Roaming\\npm\\gemini.CMD",
            "--version",
            platform_name="nt",
        )
        self.assertIn("/c", [item.lower() for item in argv])
        self.assertTrue(argv[-2].lower().endswith("gemini.cmd"))
        self.assertEqual(argv[-1], "--version")

    def test_workspace_copy_normalizes_filemode_but_still_requires_clean_content(self) -> None:
        import inspect

        source = inspect.getsource(runner.main)
        self.assertIn('core.fileMode", "false"', source)
        self.assertIn('"diff", "--quiet", "--ignore-submodules"', source)
        self.assertIn("workspace_content_diff", source)

    def test_provider_free_gate_requires_both_controls(self) -> None:
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

    def test_prompt_preserves_no_commit_and_independent_verification_boundary(self) -> None:
        prompt = runner._gemini_prompt("fix the thing")
        self.assertIn("Do not commit", prompt)
        self.assertIn("independent verification", prompt)
        self.assertIn("<task>", prompt)
        self.assertIn("fix the thing", prompt)

    def test_verifier_outcomes_are_quality_neutral(self) -> None:
        for field, expected in (("resolved_ids", "RESOLVED"), ("unresolved_ids", "TESTS_FAILED")):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "report.json"
                path.write_text(json.dumps({field: [runner.DEFAULT_INSTANCE]}), encoding="utf-8")
                self.assertEqual(runner.verifier_outcome(path, runner.DEFAULT_INSTANCE), expected)

    def test_task_helper_cross_checks_dataset_and_task_repo_identity(self) -> None:
        self.assertIn('load_task_repo("/opt/swe-bench-tasks"', runner._TASK_HELPER)
        self.assertIn("task identity mismatch", runner._TASK_HELPER)
        self.assertIn('"problem_statement"', runner._TASK_HELPER)

    def test_verifier_helper_uses_official_harness(self) -> None:
        self.assertIn("swebench.harness.run_evaluation", runner._VERIFIER_HELPER)
        self.assertIn('load_task_repo("/opt/swe-bench-tasks"', runner._VERIFIER_HELPER)


if __name__ == "__main__":
    unittest.main()
