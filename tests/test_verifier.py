import sys
import tempfile
import unittest
from pathlib import Path

from arkx.verification import TestResultStatus
from arkx.verifier import VerificationErrorKind, run_verification_command


class VerifierTests(unittest.TestCase):
    def test_passes_declared_command_and_preserves_observation(self):
        with tempfile.TemporaryDirectory() as directory:
            observed = run_verification_command(
                (sys.executable, "-c", "print('verified')"),
                workspace=directory,
                test_id="smoke",
                evidence_ref="evidence://smoke",
            )
        self.assertEqual(observed.result.status, TestResultStatus.PASSED)
        self.assertEqual(observed.result.exit_code, 0)
        self.assertIn("verified", observed.stdout)
        self.assertEqual(observed.result.command[0], sys.executable)

    def test_failure_is_not_success(self):
        with tempfile.TemporaryDirectory() as directory:
            observed = run_verification_command(
                (sys.executable, "-c", "import sys; sys.exit(3)"),
                workspace=directory,
                test_id="failure",
            )
        self.assertEqual(observed.result.status, TestResultStatus.FAILED)
        self.assertEqual(observed.result.exit_code, 3)

    def test_timeout_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            observed = run_verification_command(
                (sys.executable, "-c", "import time; time.sleep(1)"),
                workspace=directory,
                test_id="timeout",
                timeout_seconds=0.01,
            )
        self.assertEqual(observed.result.status, TestResultStatus.UNKNOWN)
        self.assertEqual(observed.error_kind, VerificationErrorKind.TIMEOUT)

    def test_missing_executable_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            observed = run_verification_command(
                ("definitely-not-installed-codepro-verifier",),
                workspace=directory,
                test_id="missing",
            )
        self.assertEqual(observed.result.status, TestResultStatus.UNKNOWN)
        self.assertEqual(observed.error_kind, VerificationErrorKind.EXECUTABLE_NOT_FOUND)

    def test_invalid_workspace_and_command_fail_closed(self):
        with self.assertRaises(ValueError):
            run_verification_command((), workspace=Path.cwd(), test_id="invalid")
        with self.assertRaises(ValueError):
            run_verification_command((sys.executable,), workspace="missing-workspace", test_id="invalid")


if __name__ == "__main__":
    unittest.main()
