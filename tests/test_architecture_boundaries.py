from pathlib import Path
import unittest


class ArchitectureBoundaryTests(unittest.TestCase):
    def test_legacy_orchestration_result_is_confined_to_compatibility_modules(self):
        source_root = Path(__file__).parents[1] / "src" / "arkx"
        violations = []
        for path in source_root.glob("*.py"):
            if path.name in {"orchestration.py", "__init__.py"}:
                continue
            text = path.read_text(encoding="utf-8")
            if "from .orchestration import ExecutionResult" in text or "from arkx.orchestration import ExecutionResult" in text:
                violations.append(path.name)
        self.assertEqual(violations, [])

    def test_public_api_exposes_distinct_neutral_and_legacy_names(self):
        import arkx
        self.assertIsNot(arkx.ExecutionResult, arkx.OrchestrationExecutionResult)
        self.assertIn("ExecutionResult", arkx.__all__)
        self.assertIn("OrchestrationExecutionResult", arkx.__all__)


if __name__ == "__main__":
    unittest.main()
