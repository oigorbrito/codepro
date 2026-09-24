import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from arkx.verification import TestResultStatus
from arkx.verifier import CommandVerifier, VerificationEvidenceStore, VerificationErrorKind, run_verification_command
from arkx.outcomes import VerificationState


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

    def test_command_verifier_persists_raw_observation_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            store = VerificationEvidenceStore(Path(directory) / "evidence")
            verifier = CommandVerifier(
                authority="local-verifier",
                workspace=directory,
                command=(sys.executable, "-c", "import time; print('raw-output'); time.sleep(0.02)"),
                test_id="smoke",
                evidence_store=store,
            )
            execution = SimpleNamespace(outcome="COMPLETED", run_id="run-1")
            first = verifier.verify(execution)
            second = verifier.verify(execution)
            self.assertEqual(first.state, VerificationState.PASS)
            self.assertEqual(second.state, VerificationState.BLOCKED)
            evidence_path = Path(directory) / "evidence" / "run-1"
            files = tuple(evidence_path.glob("verification-*.json"))
            self.assertEqual(len(files), 1)
            self.assertIn("raw-output", files[0].read_text(encoding="utf-8"))

    def test_command_verifier_does_not_accept_failed_command(self):
        with tempfile.TemporaryDirectory() as directory:
            verifier = CommandVerifier(
                authority="local-verifier",
                workspace=directory,
                command=(sys.executable, "-c", "import sys; sys.exit(2)"),
                test_id="failure",
                evidence_store=VerificationEvidenceStore(Path(directory) / "evidence"),
            )
            result = verifier.verify(SimpleNamespace(outcome="COMPLETED", run_id="run-2"))
        self.assertEqual(result.state, VerificationState.FAIL)

    def test_command_verifier_blocks_when_evidence_cannot_be_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            class FailingStore:
                def persist(self, run_id, observation):
                    raise OSError("read-only")

            verifier = CommandVerifier(
                authority="local-verifier",
                workspace=directory,
                command=(sys.executable, "-c", "print('verified')"),
                test_id="smoke",
                evidence_store=FailingStore(),
            )
            result = verifier.verify(SimpleNamespace(outcome="COMPLETED", run_id="run-3"))
        self.assertEqual(result.state, VerificationState.BLOCKED)


if __name__ == "__main__":
    unittest.main()
