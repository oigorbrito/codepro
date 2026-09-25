import io
import json
import subprocess
import sys
import tomllib
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from pathlib import Path

from arkx import __version__
from arkx.cli import main
from arkx.project import ProjectInspection


ROOT = Path(__file__).parents[1]


class CliFunctionTests(unittest.TestCase):
    def capture(self, argv):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(argv)
        return code, output.getvalue()

    def test_no_args_prints_help_and_succeeds(self):
        code, output = self.capture([])
        self.assertEqual(code, 0)
        self.assertIn("usage: codepro", output)
        self.assertIn("doctor", output)
        self.assertIn("inspect", output)

    def test_help_succeeds(self):
        result = subprocess.run(
            [sys.executable, "-m", "arkx", "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("usage: codepro", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_version_is_explicit_and_stable(self):
        result = subprocess.run(
            [sys.executable, "-m", "arkx", "--version"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), f"codepro {__version__}")
        self.assertEqual(result.stderr, "")

    def test_doctor_succeeds_on_supported_interpreter(self):
        code, output = self.capture(["doctor"])
        self.assertEqual(code, 0)
        self.assertIn("python: PASS", output)
        self.assertIn("core: PASS (importable)", output)
        self.assertTrue(output.rstrip().endswith("status: PASS"))

    def test_inspect_text_output_is_read_only_and_explicit(self):
        inspection = ProjectInspection(
            project_name="fixture",
            project_root="/tmp/fixture",
            git_available=True,
            git_repository=True,
            branch="main",
            languages=("Python",),
            test_surfaces=("tests",),
            executors=(
                ("Codex", "codex", True),
                ("Claude Code", "claude", False),
                ("Gemini CLI", "gemini", False),
            ),
        )
        with patch("arkx.cli.inspect_project", return_value=inspection):
            code, output = self.capture(["inspect"])
        self.assertEqual(code, 0)
        self.assertIn("Project: fixture", output)
        self.assertIn("Branch: main", output)
        self.assertIn("Languages: Python", output)
        self.assertIn("Codex: available (codex)", output)
        self.assertIn("Claude Code: unavailable (claude)", output)

    def test_inspect_json_output_is_canonical(self):
        inspection = ProjectInspection(
            project_name="fixture",
            project_root="/tmp/fixture",
            git_available=False,
            git_repository=False,
            branch=None,
            languages=(),
            test_surfaces=(),
            executors=(),
        )
        with patch("arkx.cli.inspect_project", return_value=inspection):
            code, output = self.capture(["inspect", "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(output.strip(), inspection.to_json())

    def test_inspect_invalid_path_returns_usage_error_code(self):
        with patch("arkx.cli.inspect_project", side_effect=ValueError("bad path")):
            result = subprocess.run(
                [sys.executable, "-m", "arkx", "inspect", "/definitely/not/here"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        # subprocess uses a separate interpreter, so exercise the function path directly too.
        with patch("arkx.cli.inspect_project", side_effect=ValueError("bad path")):
            output = io.StringIO()
            error = io.StringIO()
            with redirect_stdout(output), patch("sys.stderr", error):
                code = main(["inspect", "/missing"])
        self.assertEqual(code, 2)
        self.assertEqual(output.getvalue(), "")
        self.assertIn("codepro: error: bad path", error.getvalue())
        self.assertEqual(result.returncode, 2)

    def test_invalid_command_fails_closed(self):
        result = subprocess.run(
            [sys.executable, "-m", "arkx", "not-a-command"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("invalid choice", result.stderr)


class PackagingContractTests(unittest.TestCase):
    def test_console_script_points_to_cli_main(self):
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(project["project"]["name"], "codepro")
        self.assertEqual(project["project"]["scripts"], {"codepro": "arkx.cli:main"})
        self.assertEqual(project["project"]["requires-python"], ">=3.12")

    def test_no_runtime_dependencies_are_declared(self):
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(project["project"]["dependencies"], [])


class RunCliTests(unittest.TestCase):
    def test_run_passes_explicit_executor_and_verifier_argv(self):
        from arkx.vertical import VerticalRunResult, VerticalRunStatus

        result = VerticalRunResult(
            run_id="request-1-deadbeef0000",
            status=VerticalRunStatus.VERIFIED,
            reason="DECLARED_VERIFIER_PASSED",
            evidence_root="/tmp/evidence",
            changed_files=("src/a.py",),
        )
        argv = [
            "run",
            "--workspace", ".",
            "--revision", "a" * 40,
            "--request-id", "request-1",
            "--task-id", "task-1",
            "--requester", "user://fixture",
            "--authority", "authority://fixture",
            "--acceptance-authority", "acceptance://reviewer",
            "--scope", "src",
            "--verifier-argv-json", '["python","-m","pytest","-q"]',
            "--",
            "codex",
            "exec",
            "--full-auto",
        ]
        output = io.StringIO()
        with patch("arkx.cli.run_vertical", return_value=result) as run_mock, redirect_stdout(output):
            code = main(argv)

        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["status"], "VERIFIED")
        kwargs = run_mock.call_args.kwargs
        self.assertEqual(kwargs["executor_argv"], ("codex", "exec", "--full-auto"))
        self.assertEqual(kwargs["verifier_argv"], ("python", "-m", "pytest", "-q"))
        self.assertEqual(kwargs["scope"], ("src",))

    def test_run_rejects_invalid_verifier_json(self):
        error = io.StringIO()
        with patch("sys.stderr", error):
            code = main([
                "run",
                "--workspace", ".",
                "--revision", "a" * 40,
                "--request-id", "request-1",
                "--task-id", "task-1",
                "--requester", "user://fixture",
                "--authority", "authority://fixture",
                "--acceptance-authority", "acceptance://reviewer",
                "--scope", "src",
                "--verifier-argv-json", "not-json",
                "--",
                "codex",
            ])
        self.assertEqual(code, 2)
        self.assertIn("not valid JSON", error.getvalue())


if __name__ == "__main__":
    unittest.main()
