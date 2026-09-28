import subprocess
import tempfile
from pathlib import Path
import unittest

from arkx.isolated_workspace import IsolatedGitWorkspace, capture_repository_state


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


class IsolatedGitWorkspaceTests(unittest.TestCase):
    def test_detached_worktree_is_clean_isolated_and_removable(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source"
            workspaces = base / "workspaces"
            source.mkdir()
            git(source, "init")
            git(source, "config", "user.email", "phase6@example.invalid")
            git(source, "config", "user.name", "Phase 6 Test")
            (source / "src").mkdir()
            (source / "src" / "value.txt").write_text("before\n", encoding="utf-8")
            git(source, "add", ".")
            git(source, "commit", "-m", "base")
            revision = git(source, "rev-parse", "HEAD")

            isolated = IsolatedGitWorkspace.create(
                source_repository=source,
                revision=revision,
                workspace_root=workspaces,
                workspace_id="task-1",
            )
            self.assertNotEqual(isolated.workspace, source)
            self.assertEqual(isolated.initial_state.revision, revision)
            self.assertTrue(isolated.initial_state.clean)

            target = isolated.workspace / "src" / "value.txt"
            target.write_text("after\n", encoding="utf-8")
            final_state = isolated.capture_state()
            self.assertEqual(final_state.revision, revision)
            self.assertFalse(final_state.clean)
            self.assertIn("src/value.txt", final_state.status_porcelain)
            self.assertEqual(
                (source / "src" / "value.txt").read_text(encoding="utf-8"),
                "before\n",
            )
            self.assertTrue(capture_repository_state(source).clean)

            cleanup = isolated.remove()
            self.assertTrue(cleanup.removed)
            self.assertFalse(isolated.workspace.exists())
            self.assertEqual(cleanup.remove.returncode, 0)
            self.assertEqual(cleanup.prune.returncode, 0)

    def test_workspace_root_inside_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir()
            git(source, "init")
            git(source, "config", "user.email", "phase6@example.invalid")
            git(source, "config", "user.name", "Phase 6 Test")
            (source / "value.txt").write_text("x\n", encoding="utf-8")
            git(source, "add", ".")
            git(source, "commit", "-m", "base")
            revision = git(source, "rev-parse", "HEAD")
            with self.assertRaisesRegex(ValueError, "outside the source repository"):
                IsolatedGitWorkspace.create(
                    source_repository=source,
                    revision=revision,
                    workspace_root=source / "nested",
                    workspace_id="task-1",
                )


if __name__ == "__main__":
    unittest.main()
