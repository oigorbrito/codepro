import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from arkx.command import (
    CommandResult,
    CommandSpec,
    EnvironmentErrorKind,
    LocalCommandEnvironment,
)


class CommandSpecTests(unittest.TestCase):
    def test_rejects_invalid_command_contract(self):
        with self.assertRaises(ValueError):
            CommandSpec((), ".", 1)
        with self.assertRaises(ValueError):
            CommandSpec(("",), ".", 1)
        with self.assertRaises(ValueError):
            CommandSpec((sys.executable,), "", 1)
        for timeout in (0, -1, float("inf"), float("nan"), True):
            with self.subTest(timeout=timeout):
                with self.assertRaises(ValueError):
                    CommandSpec((sys.executable,), ".", timeout)

    def test_serialization_is_deterministic_and_round_trips(self):
        spec = CommandSpec(
            (sys.executable, "-c", "print('x')"),
            ".",
            2.5,
        )
        self.assertEqual(spec.to_json(), spec.to_json())
        restored = CommandSpec.from_json(spec.to_json())
        self.assertEqual(restored, spec)
        self.assertEqual(json.loads(spec.to_json())["schema_version"], 1)


class LocalCommandEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.environment = LocalCommandEnvironment()

    def execute_python(self, source, *, cwd, timeout=5):
        return self.environment.execute(
            CommandSpec(
                (sys.executable, "-c", source),
                str(cwd),
                timeout,
            )
        )

    def test_exit_zero_captures_stdout_and_stderr_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.execute_python(
                "import sys; print('out'); print('err', file=sys.stderr)",
                cwd=directory,
            )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout, "out\n")
        self.assertEqual(result.stderr, "err\n")
        self.assertFalse(result.timed_out)
        self.assertIsNone(result.environment_error)
        self.assertTrue(result.process_started)

    def test_nonzero_exit_is_observed_without_task_status_inference(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.execute_python(
                "import sys; print('reproduced'); raise SystemExit(7)",
                cwd=directory,
            )
        self.assertEqual(result.exit_code, 7)
        self.assertEqual(result.stdout, "reproduced\n")
        self.assertFalse(result.timed_out)
        self.assertIsNone(result.environment_error)
        payload = result.to_dict()
        self.assertNotIn("status", payload)
        self.assertNotIn("success", payload)
        self.assertNotIn("failed", payload)

    def test_cwd_is_explicit_and_recorded_as_absolute_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            result = self.execute_python(
                "import os; print(os.getcwd())",
                cwd=root,
            )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), str(root))
        self.assertEqual(result.cwd, str(root))

    def test_argv_is_executed_without_shell_interpretation(self):
        with tempfile.TemporaryDirectory() as directory:
            literal = "x; echo shell-was-used"
            result = self.environment.execute(
                CommandSpec(
                    (
                        sys.executable,
                        "-c",
                        "import sys; print(sys.argv[1])",
                        literal,
                    ),
                    directory,
                    5,
                )
            )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.strip(), literal)
        self.assertNotIn("\nshell-was-used", result.stdout)

    def test_missing_executable_is_environment_error_not_command_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.environment.execute(
                CommandSpec(
                    ("codepro-definitely-not-an-executable-7f85c2",),
                    directory,
                    5,
                )
            )
        self.assertIsNone(result.exit_code)
        self.assertFalse(result.timed_out)
        self.assertFalse(result.process_started)
        self.assertIsNotNone(result.environment_error)
        self.assertEqual(
            result.environment_error.kind,
            EnvironmentErrorKind.EXECUTABLE_NOT_FOUND,
        )

    def test_missing_cwd_is_environment_error(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing"
            result = self.environment.execute(
                CommandSpec((sys.executable, "-c", "print(1)"), str(missing), 5)
            )
        self.assertIsNone(result.exit_code)
        self.assertFalse(result.process_started)
        self.assertEqual(
            result.environment_error.kind,
            EnvironmentErrorKind.CWD_UNAVAILABLE,
        )

    def test_timeout_is_distinct_from_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.execute_python(
                "import time; print('before', flush=True); time.sleep(5)",
                cwd=directory,
                timeout=0.15,
            )
        self.assertTrue(result.timed_out)
        self.assertTrue(result.process_started)
        self.assertIn("before", result.stdout)
        self.assertIsInstance(result.exit_code, int)
        self.assertLess(result.duration_ms, 3000)

    @unittest.skipUnless(os.name == "posix", "process-group cleanup assertion is POSIX-specific")
    def test_timeout_kills_child_process_group(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child_pid_file = root / "child.pid"
            source = (
                "import pathlib, subprocess, sys, time; "
                "p=subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)']); "
                f"pathlib.Path({str(child_pid_file)!r}).write_text(str(p.pid)); "
                "time.sleep(30)"
            )
            result = self.execute_python(source, cwd=root, timeout=0.25)
            self.assertTrue(result.timed_out)
            child_pid = int(child_pid_file.read_text(encoding="utf-8"))

            deadline = time.monotonic() + 3
            while time.monotonic() < deadline and _process_running(child_pid):
                time.sleep(0.05)
            self.assertFalse(
                _process_running(child_pid),
                "timed-out command left a live child process",
            )

    def test_result_serialization_round_trip_preserves_observation(self):
        value = CommandResult(
            argv=("example", "--flag"),
            cwd="/tmp/example",
            exit_code=3,
            stdout="out",
            stderr="err",
            timed_out=False,
            duration_ms=12,
        )
        restored = CommandResult.from_json(value.to_json())
        self.assertEqual(restored, value)
        self.assertEqual(value.to_json(), value.to_json())


def _process_running(pid: int) -> bool:
    stat = Path(f"/proc/{pid}/stat")
    if stat.exists():
        try:
            fields = stat.read_text(encoding="utf-8").split()
        except OSError:
            fields = []
        if len(fields) > 2 and fields[2] == "Z":
            return False

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


if __name__ == "__main__":
    unittest.main()
