from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "run_mini_v246_verifier_controls.py"
SPEC = importlib.util.spec_from_file_location("mini_v246_verifier_controls", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class MiniV246VerifierControlsTests(unittest.TestCase):
    def test_negative_patch_is_nonempty_and_behavior_inert(self) -> None:
        self.assertIn(".codepro-verifier-negative-control.txt", runner.NEGATIVE_PATCH)
        self.assertNotIn("sympy/", runner.NEGATIVE_PATCH)
        self.assertTrue(runner.NEGATIVE_PATCH.startswith("diff --git"))

    def test_classifies_unresolved_as_tests_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            path.write_text(
                json.dumps({"unresolved_ids": ["sympy__sympy-14711"]}),
                encoding="utf-8",
            )
            result = runner._classify_report(path, "sympy__sympy-14711")
        self.assertEqual(result["status"], "TESTS_FAILED")
        self.assertFalse(result["raw_outcome"])

    def test_classifies_resolved_as_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            path.write_text(
                json.dumps({"resolved_ids": ["sympy__sympy-14711"]}),
                encoding="utf-8",
            )
            result = runner._classify_report(path, "sympy__sympy-14711")
        self.assertEqual(result["status"], "RESOLVED")
        self.assertTrue(result["raw_outcome"])

    def test_linux_helper_derives_only_official_image_identity(self) -> None:
        self.assertIn("from swebench.task.checks import expected_image", runner._LINUX_HELPER)
        self.assertIn('instance["image"] = derived_image', runner._LINUX_HELPER)
        self.assertIn("dataset image mismatch", runner._LINUX_HELPER)

    def test_subprocess_capture_is_utf8_tolerant(self) -> None:
        import inspect

        source = inspect.getsource(runner.run)
        self.assertIn('encoding="utf-8"', source)
        self.assertIn('errors="replace"', source)

    def test_empty_patch_filter_does_not_count_as_negative_control(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            path.write_text(
                json.dumps({"empty_patch_ids": ["sympy__sympy-14711"]}),
                encoding="utf-8",
            )
            result = runner._classify_report(path, "sympy__sympy-14711")
        self.assertEqual(result["status"], "NOT_EXECUTED")


if __name__ == "__main__":
    unittest.main()
