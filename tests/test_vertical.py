import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from arkx.vertical import VerticalRunStatus, run_vertical


class VerticalRunTests(unittest.TestCase):
    def init_repo(self, root: Path) -> str:
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "CodePro Test"], cwd=root, check=True)
        (root / "src").mkdir()
        (root / "src" / "value.txt").write_text("before\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(["git", "commit", "-m", "base"], cwd=root, check=True, capture_output=True)
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def test_one_authorized_command_can_execute_verify_and_persist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            evidence = Path(tmp) / "evidence"
            root.mkdir()
            revision = self.init_repo(root)

            result = run_vertical(
                workspace=root,
                revision=revision,
                request_id="request-1",
                task_id="task-1",
                requester_ref="user://fixture",
                authority_ref="authority://fixture",
                acceptance_authority_ref="acceptance://reviewer",
                scope=("src",),
                executor_argv=(
                    sys.executable,
                    "-c",
                    "from pathlib import Path; Path('src/value.txt').write_text('after\\n', encoding='utf-8')",
                ),
                verifier_argv=(
                    sys.executable,
                    "-c",
                    "from pathlib import Path; raise SystemExit(0 if Path('src/value.txt').read_text() == 'after\\n' else 1)",
                ),
                evidence_dir=evidence,
                max_wall_time_seconds=30,
            )

            self.assertEqual(result.status, VerticalRunStatus.VERIFIED)
            run_root = Path(result.evidence_root)
            self.assertTrue((run_root / "request.json").is_file())
            self.assertTrue((run_root / "authority-grant.json").is_file())
            self.assertTrue((run_root / "execution.json").is_file())
            self.assertTrue((run_root / "workspace.patch").is_file())
            self.assertTrue((run_root / "verification-summary.json").is_file())
            self.assertEqual(
                json.loads((run_root / "result.json").read_text(encoding="utf-8"))["status"],
                "VERIFIED",
            )

    def test_revision_mismatch_blocks_before_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            self.init_repo(root)
            result = run_vertical(
                workspace=root,
                revision="0" * 40,
                request_id="request-2",
                task_id="task-2",
                requester_ref="user://fixture",
                authority_ref="authority://fixture",
                acceptance_authority_ref="acceptance://reviewer",
                scope=("src",),
                executor_argv=(sys.executable, "-c", "raise SystemExit(0)"),
                verifier_argv=(sys.executable, "-c", "raise SystemExit(0)"),
                evidence_dir=Path(tmp) / "evidence",
            )
            self.assertEqual(result.status, VerticalRunStatus.BLOCKED)
            self.assertEqual(result.reason, "REVISION_MISMATCH")

    def test_scope_violation_blocks_before_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            revision = self.init_repo(root)
            result = run_vertical(
                workspace=root,
                revision=revision,
                request_id="request-3",
                task_id="task-3",
                requester_ref="user://fixture",
                authority_ref="authority://fixture",
                acceptance_authority_ref="acceptance://reviewer",
                scope=("src",),
                executor_argv=(
                    sys.executable,
                    "-c",
                    "from pathlib import Path; Path('outside.txt').write_text('x', encoding='utf-8')",
                ),
                verifier_argv=(sys.executable, "-c", "raise SystemExit(0)"),
                evidence_dir=Path(tmp) / "evidence",
            )
            self.assertEqual(result.status, VerticalRunStatus.BLOCKED)
            self.assertEqual(result.reason, "CHANGED_FILES_OUTSIDE_AUTHORIZED_SCOPE")

    def test_evidence_inside_workspace_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            revision = self.init_repo(root)
            with self.assertRaisesRegex(ValueError, "outside the target workspace"):
                run_vertical(
                    workspace=root,
                    revision=revision,
                    request_id="request-4",
                    task_id="task-4",
                    requester_ref="user://fixture",
                    authority_ref="authority://fixture",
                    acceptance_authority_ref="acceptance://reviewer",
                    scope=("src",),
                    executor_argv=(sys.executable, "-c", "raise SystemExit(0)"),
                    verifier_argv=(sys.executable, "-c", "raise SystemExit(0)"),
                    evidence_dir=root / ".codepro" / "runs",
                )

    def test_nonzero_executor_exit_cannot_be_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            revision = self.init_repo(root)
            result = run_vertical(
                workspace=root,
                revision=revision,
                request_id="request-failed",
                task_id="task-failed",
                requester_ref="user://fixture",
                authority_ref="authority://fixture",
                acceptance_authority_ref="acceptance://reviewer",
                scope=("src",),
                executor_argv=(sys.executable, "-c", "raise SystemExit(7)"),
                verifier_argv=(sys.executable, "-c", "raise SystemExit(0)"),
                evidence_dir=Path(tmp) / "evidence",
                attempt_id="attempt-failed",
            )
            self.assertEqual(result.status, VerticalRunStatus.FAILED)
            self.assertEqual(result.reason, "EXECUTOR_EXIT_NONZERO:7")

    def test_timeout_is_distinct_from_generic_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            revision = self.init_repo(root)
            result = run_vertical(
                workspace=root,
                revision=revision,
                request_id="request-timeout",
                task_id="task-timeout",
                requester_ref="user://fixture",
                authority_ref="authority://fixture",
                acceptance_authority_ref="acceptance://reviewer",
                scope=("src",),
                executor_argv=(sys.executable, "-c", "import time; time.sleep(2)"),
                verifier_argv=(sys.executable, "-c", "raise SystemExit(0)"),
                evidence_dir=Path(tmp) / "evidence",
                max_wall_time_seconds=0.1,
                attempt_id="attempt-timeout",
            )
            self.assertEqual(result.status, VerticalRunStatus.TIMED_OUT)

    def test_missing_executor_is_environment_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            revision = self.init_repo(root)
            result = run_vertical(
                workspace=root,
                revision=revision,
                request_id="request-env",
                task_id="task-env",
                requester_ref="user://fixture",
                authority_ref="authority://fixture",
                acceptance_authority_ref="acceptance://reviewer",
                scope=("src",),
                executor_argv=("codepro-definitely-missing-executable-7f4d",),
                verifier_argv=(sys.executable, "-c", "raise SystemExit(0)"),
                evidence_dir=Path(tmp) / "evidence",
                attempt_id="attempt-env",
            )
            self.assertEqual(result.status, VerticalRunStatus.ENVIRONMENT_UNAVAILABLE)

    def test_attempt_id_produces_distinct_run_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            revision = self.init_repo(root)
            common = dict(
                workspace=root,
                revision=revision,
                request_id="request-repeat",
                task_id="task-repeat",
                requester_ref="user://fixture",
                authority_ref="authority://fixture",
                acceptance_authority_ref="acceptance://reviewer",
                scope=("src",),
                executor_argv=(sys.executable, "-c", "raise SystemExit(0)"),
                verifier_argv=(sys.executable, "-c", "raise SystemExit(0)"),
            )
            first = run_vertical(**common, evidence_dir=Path(tmp) / "evidence-a", attempt_id="attempt-1")
            second = run_vertical(**common, evidence_dir=Path(tmp) / "evidence-b", attempt_id="attempt-2")
            self.assertNotEqual(first.run_id, second.run_id)
            self.assertEqual(first.attempt_id, "attempt-1")
            self.assertEqual(second.attempt_id, "attempt-2")

    def test_successful_noop_is_blocked_before_verifier(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            revision = self.init_repo(root)
            result = run_vertical(
                workspace=root,
                revision=revision,
                request_id="request-noop",
                task_id="task-noop",
                requester_ref="user://fixture",
                authority_ref="authority://fixture",
                acceptance_authority_ref="acceptance://reviewer",
                scope=("src",),
                executor_argv=(sys.executable, "-c", "raise SystemExit(0)"),
                verifier_argv=(sys.executable, "-c", "raise SystemExit(0)"),
                evidence_dir=Path(tmp) / "evidence",
            )
            self.assertEqual(result.status, VerticalRunStatus.BLOCKED)
            self.assertEqual(result.reason, "NO_OBSERVABLE_CHANGE")
            self.assertFalse((Path(result.evidence_root) / "verification-summary.json").exists())

    def test_total_wall_budget_can_expire_before_verifier(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            revision = self.init_repo(root)
            with patch("arkx.vertical.time.monotonic", side_effect=(100.0, 102.0)):
                result = run_vertical(
                    workspace=root,
                    revision=revision,
                    request_id="request-budget",
                    task_id="task-budget",
                    requester_ref="user://fixture",
                    authority_ref="authority://fixture",
                    acceptance_authority_ref="acceptance://reviewer",
                    scope=("src",),
                    executor_argv=(
                        sys.executable,
                        "-c",
                        "from pathlib import Path; Path('src/value.txt').write_text('after\\n', encoding='utf-8')",
                    ),
                    verifier_argv=(sys.executable, "-c", "raise SystemExit(0)"),
                    evidence_dir=Path(tmp) / "evidence",
                    max_wall_time_seconds=1.0,
                )
            self.assertEqual(result.status, VerticalRunStatus.TIMED_OUT)
            self.assertEqual(result.reason, "TOTAL_WALL_TIME_EXHAUSTED_BEFORE_VERIFIER")
            budget = json.loads(
                (Path(result.evidence_root) / "wall-time-budget.json").read_text(encoding="utf-8")
            )
            self.assertEqual(budget["remaining_before_verifier_seconds"], 0.0)

    def test_rename_with_space_preserves_source_and_destination_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            revision = self.init_repo(root)
            result = run_vertical(
                workspace=root,
                revision=revision,
                request_id="request-rename",
                task_id="task-rename",
                requester_ref="user://fixture",
                authority_ref="authority://fixture",
                acceptance_authority_ref="acceptance://reviewer",
                scope=("src",),
                executor_argv=(
                    sys.executable,
                    "-c",
                    "from pathlib import Path; Path('src/value.txt').rename('src/value with space.txt')",
                ),
                verifier_argv=(sys.executable, "-c", "raise SystemExit(0)"),
                evidence_dir=Path(tmp) / "evidence",
            )
            self.assertEqual(result.status, VerticalRunStatus.VERIFIED)
            self.assertEqual(
                set(result.changed_files),
                {"src/value.txt", "src/value with space.txt"},
            )


if __name__ == "__main__":
    unittest.main()
