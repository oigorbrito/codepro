from pathlib import Path
import os
import subprocess
import sys
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

    def test_root_import_does_not_eagerly_load_experimental_subsystems(self):
        probe = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; import arkx; print('\\n'.join(sorted(k for k in sys.modules if k.startswith('arkx.'))))",
            ],
            check=True,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )
        loaded = set(probe.stdout.splitlines())
        self.assertNotIn("arkx.p82", loaded)
        self.assertNotIn("arkx.p82_baseline", loaded)
        self.assertNotIn("arkx.composition", loaded)
        self.assertNotIn("arkx.executor_qualification", loaded)
        self.assertNotIn("arkx.swebench_authority", loaded)

    def test_legacy_root_export_is_lazy_and_compatible(self):
        probe = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; import arkx; from arkx import Event; print(Event.__module__); print('arkx.contracts' in sys.modules); print('arkx.event_log' in sys.modules)",
            ],
            check=True,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )
        self.assertEqual(probe.stdout.splitlines(), ["arkx.contracts", "True", "False"])

    def test_legacy_public_manifest_resolves_every_declared_name(self):
        import arkx

        self.assertEqual(len(arkx.__all__), 259)
        for name in arkx.__all__:
            with self.subTest(name=name):
                self.assertIsNotNone(getattr(arkx, name))

    def test_legacy_wildcard_import_preserves_public_manifest(self):
        probe = subprocess.run(
            [
                sys.executable,
                "-c",
                "import arkx; namespace={}; exec('from arkx import *', namespace); print(len(namespace)); print('compare_qualification_trials' in namespace)",
            ],
            check=True,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )
        self.assertEqual(probe.stdout.splitlines(), ["258", "True"])


if __name__ == "__main__":
    unittest.main()
