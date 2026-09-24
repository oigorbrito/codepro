import contextlib
import io
import json
import unittest
from unittest.mock import patch

from arkx.cli import main


class CliTests(unittest.TestCase):
    def test_doctor_json_reports_packaged_runtime(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(["doctor", "--json"])
        payload = json.loads(output.getvalue())
        self.assertEqual(status, 0)
        self.assertEqual(payload["package"], "codepro")
        self.assertEqual(payload["version"], "0.3.0.dev0")
        self.assertTrue(payload["python_supported"])
        self.assertEqual(payload["status"], "PASS")

    def test_doctor_fails_outside_supported_python_range(self):
        output = io.StringIO()
        with patch("arkx.cli.sys.version_info", (3, 11)), contextlib.redirect_stdout(output):
            status = main(["doctor", "--json"])
        payload = json.loads(output.getvalue())
        self.assertEqual(status, 1)
        self.assertFalse(payload["python_supported"])
        self.assertEqual(payload["status"], "FAIL")

    def test_baseline_delegates_to_deterministic_fixture(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main(["baseline"])
        payload = json.loads(output.getvalue())
        self.assertEqual(status, 0)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["executor_id"], "fixture")

    def test_no_command_is_not_a_product_execution(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main([])
        self.assertEqual(status, 2)
        self.assertIn("baseline", output.getvalue())

    def test_task_submission_command_is_not_available(self):
        error = io.StringIO()
        with contextlib.redirect_stderr(error):
            with self.assertRaises(SystemExit) as raised:
                main(["run"])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("invalid choice", error.getvalue())


if __name__ == "__main__":
    unittest.main()
