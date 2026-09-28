import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from arkx.project import inspect_project


class ProjectInspectionTests(unittest.TestCase):
    def test_detects_git_markers_tests_and_known_executors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pyproject.toml").write_text("[project]\nname='fixture'\n", encoding="utf-8")
            (root / "tests").mkdir()

            def which(command):
                return {
                    "git": "/usr/bin/git",
                    "codex": "/usr/local/bin/codex",
                    "claude": None,
                    "gemini": "/usr/local/bin/gemini",
                }.get(command)

            def runner(command, **kwargs):
                tail = command[3:]
                if tail == ["rev-parse", "--show-toplevel"]:
                    return subprocess.CompletedProcess(command, 0, stdout=str(root) + "\n", stderr="")
                if tail == ["branch", "--show-current"]:
                    return subprocess.CompletedProcess(command, 0, stdout="main\n", stderr="")
                raise AssertionError(f"unexpected git command: {command}")

            result = inspect_project(root, which=which, runner=runner)

            self.assertEqual(result.project_name, root.name)
            self.assertEqual(result.project_root, str(root.resolve()))
            self.assertTrue(result.git_available)
            self.assertTrue(result.git_repository)
            self.assertEqual(result.branch, "main")
            self.assertEqual(result.languages, ("Python",))
            self.assertEqual(result.test_surfaces, ("tests",))
            self.assertEqual(
                result.executors,
                (
                    ("Codex", "codex", True),
                    ("Claude Code", "claude", False),
                    ("Gemini CLI", "gemini", True),
                ),
            )

            payload = json.loads(result.to_json())
            self.assertEqual(payload["branch"], "main")
            self.assertEqual(payload["languages"], ["Python"])
            self.assertTrue(payload["executors"][0]["available"])

    def test_non_git_directory_remains_inspectable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "go.mod").write_text("module example.test/project\n", encoding="utf-8")

            result = inspect_project(root, which=lambda command: None)

            self.assertFalse(result.git_available)
            self.assertFalse(result.git_repository)
            self.assertIsNone(result.branch)
            self.assertEqual(result.languages, ("Go",))
            self.assertEqual(result.project_root, str(root.resolve()))

    def test_multiple_language_markers_have_stable_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("package.json", "tsconfig.json", "Cargo.toml", "pyproject.toml"):
                (root / name).write_text("{}\n", encoding="utf-8")

            result = inspect_project(root, which=lambda command: None)

            self.assertEqual(
                result.languages,
                ("Python", "TypeScript", "JavaScript", "Rust"),
            )

    def test_invalid_path_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            with self.assertRaises(ValueError):
                inspect_project(missing, which=lambda command: None)


if __name__ == "__main__":
    unittest.main()
