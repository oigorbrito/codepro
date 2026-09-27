from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).parents[1]
RUNNER_PATH = ROOT / "tools" / "run_mini_v246_runtime_access.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("run_mini_v246_runtime_access", RUNNER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimeAccessRunnerTests(unittest.TestCase):
    def test_frozen_reference_identity(self):
        runner = load_runner()
        self.assertEqual(runner.MINI_VERSION, "v2.4.6")
        self.assertEqual(
            runner.MINI_SHA,
            "a83fcae82d2a08f0ee0c688f9d137b3566c097f8",
        )
        self.assertEqual(
            runner.MINI_CONFIG_BLOB,
            "106decd160e72e5164e29d15d23da354c29c309d",
        )

    def test_gate_keeps_disallowed_work_not_executed(self):
        text = RUNNER_PATH.read_text(encoding="utf-8")
        for marker in (
            '"no_op": "NOT_EXECUTED"',
            '"gold_oracle": "NOT_EXECUTED"',
            '"provider_model": "NOT_EXECUTED"',
            '"benchmark": "NOT_EXECUTED"',
            '"executor_promotion": "NOT_AUTHORIZED"',
        ):
            self.assertIn(marker, text)

    def test_run_never_uses_shell(self):
        runner = load_runner()
        completed = type(
            "Completed",
            (),
            {"returncode": 0, "stdout": "ok", "stderr": ""},
        )()
        with patch.object(runner.subprocess, "run", return_value=completed) as mocked:
            result = runner.run(["echo", "ok"])
        self.assertEqual(result["returncode"], 0)
        self.assertFalse(mocked.call_args.kwargs["shell"])


if __name__ == "__main__":
    unittest.main()
