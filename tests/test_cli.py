import io
import subprocess
import sys
import tomllib
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from arkx import __version__
from arkx.cli import main


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
        self.assertIn("usage: dekon", output)
        self.assertIn("doctor", output)

    def test_help_succeeds(self):
        result = subprocess.run(
            [sys.executable, "-m", "arkx", "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("usage: dekon", result.stdout)
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
        self.assertEqual(result.stdout.strip(), f"dekon {__version__}")
        self.assertEqual(result.stderr, "")

    def test_doctor_succeeds_on_supported_interpreter(self):
        code, output = self.capture(["doctor"])
        self.assertEqual(code, 0)
        self.assertIn("python: PASS", output)
        self.assertIn("core: PASS (importable)", output)
        self.assertTrue(output.rstrip().endswith("status: PASS"))

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
        self.assertEqual(project["project"]["name"], "dekon")
        self.assertEqual(project["project"]["scripts"], {"dekon": "arkx.cli:main"})
        self.assertEqual(project["project"]["requires-python"], ">=3.12")

    def test_no_runtime_dependencies_are_declared(self):
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(project["project"]["dependencies"], [])


if __name__ == "__main__":
    unittest.main()
