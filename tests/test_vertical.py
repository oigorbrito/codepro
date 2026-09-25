import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

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


if __name__ == "__main__":
    unittest.main()
