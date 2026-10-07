import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools" / "run_chassis_ci_contract.py"


class ChassisCiContractTests(unittest.TestCase):
    def _run(self, candidate_code: str, verifier_code: str):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            output = td / "evidence" / "result.json"
            cmd = [
                sys.executable,
                str(RUNNER),
                "--candidate", "fixture",
                "--candidate-revision", "fixture-sha",
                "--candidate-command-json", json.dumps([sys.executable, "-c", candidate_code]),
                "--verifier-command-json", json.dumps([sys.executable, "-c", verifier_code]),
                "--workdir", str(td / "work"),
                "--output", str(output),
                "--timeout-seconds", "5",
            ]
            cp = subprocess.run(cmd, text=True, capture_output=True, check=False)
            self.assertTrue(output.exists(), cp.stderr)
            return cp, json.loads(output.read_text(encoding="utf-8"))

    def test_verified_pass_is_owned_by_verifier_not_candidate_exit(self):
        candidate = "from pathlib import Path; Path('ok.txt').write_text('ok')"
        verifier = "from pathlib import Path; raise SystemExit(0 if Path('ok.txt').read_text() == 'ok' else 1)"
        cp, rec = self._run(candidate, verifier)
        self.assertEqual(cp.returncode, 0)
        self.assertEqual(rec["classification"], "VERIFIED_PASS")
        self.assertEqual(rec["verifier_result"], "PASS")
        self.assertFalse(rec["invariants"]["candidate_exit_is_task_success"])

    def test_broken_candidate_fails_closed(self):
        candidate = "print('no repair performed')"
        verifier = "from pathlib import Path; raise SystemExit(0 if Path('ok.txt').exists() else 1)"
        cp, rec = self._run(candidate, verifier)
        self.assertEqual(cp.returncode, 2)
        self.assertEqual(rec["classification"], "VERIFIED_FAIL")
        self.assertEqual(rec["verifier_result"], "FAIL")

    def test_nonzero_candidate_can_still_be_verified_if_workspace_is_correct(self):
        candidate = "from pathlib import Path; Path('ok.txt').write_text('ok'); raise SystemExit(7)"
        verifier = "from pathlib import Path; raise SystemExit(0 if Path('ok.txt').read_text() == 'ok' else 1)"
        cp, rec = self._run(candidate, verifier)
        self.assertEqual(rec["candidate_observation"]["exit_code"], 7)
        self.assertEqual(cp.returncode, 0)
        self.assertEqual(rec["classification"], "VERIFIED_PASS")

    def test_missing_executable_is_infrastructure_failure(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            output = td / "result.json"
            cmd = [
                sys.executable, str(RUNNER),
                "--candidate", "fixture",
                "--candidate-revision", "fixture-sha",
                "--candidate-command-json", json.dumps(["definitely-not-a-real-command-xyz"]),
                "--verifier-command-json", json.dumps([sys.executable, "-c", "raise SystemExit(0)"]),
                "--workdir", str(td / "work"),
                "--output", str(output),
                "--timeout-seconds", "5",
            ]
            cp = subprocess.run(cmd, text=True, capture_output=True, check=False)
            rec = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(cp.returncode, 3)
        self.assertEqual(rec["classification"], "INFRA_FAILURE")
        self.assertEqual(rec["verifier_result"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
