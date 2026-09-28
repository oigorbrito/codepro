import sys
import tempfile
from pathlib import Path
import unittest

from arkx.repository_operations import RepositoryOperationKind, RepositoryToolbox


class RepositoryToolboxTests(unittest.TestCase):
    def test_inspect_edit_and_command_are_explicit_observations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            target = root / "src" / "value.txt"
            target.write_text("before\n", encoding="utf-8")

            toolbox = RepositoryToolbox(root, authorized_scope=("src",))
            inspected = toolbox.inspect("src/value.txt")
            self.assertEqual(inspected.kind, RepositoryOperationKind.INSPECT)
            self.assertEqual(inspected.stdout, "before\n")
            self.assertEqual(inspected.exit_code, 0)
            self.assertIsNotNone(inspected.content_sha256)

            edited = toolbox.edit("src/value.txt", "after\n")
            self.assertEqual(edited.kind, RepositoryOperationKind.EDIT)
            self.assertEqual(target.read_text(encoding="utf-8"), "after\n")
            self.assertEqual(edited.bytes_observed, len("after\n".encode("utf-8")))

            command = toolbox.command(
                (sys.executable, "-c", "print('COMMAND_OK')"),
                timeout_seconds=5,
            )
            self.assertEqual(command.kind, RepositoryOperationKind.COMMAND)
            self.assertEqual(command.exit_code, 0)
            self.assertEqual(command.stdout.strip(), "COMMAND_OK")
            self.assertFalse(command.timed_out)

    def test_repository_paths_cannot_escape_scope_or_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "value.txt").write_text("value\n", encoding="utf-8")
            (root / "outside.txt").write_text("outside\n", encoding="utf-8")
            toolbox = RepositoryToolbox(root, authorized_scope=("src",))

            with self.assertRaisesRegex(ValueError, "outside authorized scope"):
                toolbox.inspect("outside.txt")
            with self.assertRaises(ValueError):
                toolbox.inspect("../outside.txt")
            with self.assertRaisesRegex(ValueError, "outside authorized scope"):
                toolbox.edit("tests/new.txt", "x")

    def test_new_file_edit_within_scope_is_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            toolbox = RepositoryToolbox(root, authorized_scope=("src",))
            observation = toolbox.edit("src/new.txt", "new\n")
            self.assertEqual(observation.kind, RepositoryOperationKind.EDIT)
            self.assertEqual(
                (root / "src" / "new.txt").read_text(encoding="utf-8"),
                "new\n",
            )


if __name__ == "__main__":
    unittest.main()
