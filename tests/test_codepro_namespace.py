import contextlib
import io
import subprocess
import sys
import unittest

import arkx
import codepro
import arkx.contracts as arkx_contracts
import arkx.orchestration as arkx_orchestration
import arkx.verification as arkx_verification
import arkx.verifier as arkx_verifier
import codepro.contracts as codepro_contracts
import codepro.orchestration as codepro_orchestration
import codepro.verification as codepro_verification
import codepro.verifier as codepro_verifier
import codepro.baseline as codepro_baseline
import codepro.performance_baseline as codepro_performance_baseline
import codepro.p82_localization as codepro_localization
from codepro.cli import main as codepro_main
from arkx.cli import main as arkx_main


class CodeproNamespaceTests(unittest.TestCase):
    def test_codepro_is_the_canonical_facade_for_the_current_public_api(self):
        self.assertEqual(codepro.__version__, arkx.__version__)
        self.assertEqual(codepro.__all__, tuple(arkx.__all__))
        for name in codepro.__all__:
            self.assertIs(getattr(codepro, name), getattr(arkx, name))

    def test_legacy_namespace_remains_available(self):
        self.assertIs(codepro.ExecutionResult, arkx.ExecutionResult)
        self.assertIs(codepro.OrchestrationExecutionResult, arkx.OrchestrationExecutionResult)

    def test_codepro_cli_is_the_canonical_entrypoint_facade(self):
        self.assertIsNot(codepro_main, arkx_main)

        canonical_output = io.StringIO()
        with contextlib.redirect_stdout(canonical_output):
            self.assertEqual(codepro_main(["doctor"]), 0)

        legacy_output = io.StringIO()
        with contextlib.redirect_stdout(legacy_output):
            self.assertEqual(arkx_main(["doctor"]), 0)

        self.assertIn("status: PASS", canonical_output.getvalue())
        self.assertIn("status: PASS", legacy_output.getvalue())

    def test_core_submodules_preserve_object_identity_during_migration(self):
        pairs = (
            (codepro_contracts, arkx_contracts),
            (codepro_orchestration, arkx_orchestration),
            (codepro_verification, arkx_verification),
            (codepro_verifier, arkx_verifier),
        )
        for canonical, legacy in pairs:
            self.assertEqual(canonical.__all__, tuple(sorted(name for name in dir(legacy) if not name.startswith("_"))))
            for name in canonical.__all__:
                self.assertIs(getattr(canonical, name), getattr(legacy, name))

    def test_operational_submodules_preserve_object_identity(self):
        import arkx.baseline as arkx_baseline
        import arkx.performance_baseline as arkx_performance_baseline
        import arkx.p82_localization as arkx_localization

        for canonical, legacy in (
            (codepro_baseline, arkx_baseline),
            (codepro_performance_baseline, arkx_performance_baseline),
            (codepro_localization, arkx_localization),
        ):
            for name in canonical.__all__:
                self.assertIs(getattr(canonical, name), getattr(legacy, name))

    def test_import_does_not_claim_migration_of_unsupported_submodules(self):
        probe = subprocess.run(
            [
                sys.executable,
                "-c",
                "import codepro, sys; print('codepro.cli' in sys.modules); print(codepro.__version__)",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(probe.stdout.splitlines(), ["False", arkx.__version__])


if __name__ == "__main__":
    unittest.main()
