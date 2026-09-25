import json
from pathlib import Path
import tempfile
import unittest

from arkx.acceptance import AcceptanceStatus
from arkx.m1_acceptance import M1_ACCEPTANCE_AUTHORITY, persist_acceptance, review_m1_doctor_json


class M1AcceptanceTests(unittest.TestCase):
    def make_bundle(self, root: Path):
        run_root = root / "run-evidence" / "m1-doctor-json-1-fixture"
        (run_root / "verification" / "m1-doctor-json-1-fixture").mkdir(parents=True)
        def write(path, value):
            path.write_text(json.dumps(value), encoding="utf-8")
        write(root / "m1-summary.json", {
            "classification": "M1_REAL_VERTICAL_VERIFIED",
            "task_ref": "github://oigorbrito/codepro/issues/57",
            "request_id": "m1-doctor-json-1",
            "task_id": "issue-57-doctor-json",
            "target_base_sha": "e401936979aea7f875508394aab1dac8f9e850d0",
            "provider_called": False,
            "model_called": False,
            "promotion": "NOT_AUTHORIZED",
            "executor": {"id": "local-command", "selection": "EXPLICIT", "fallback_allowed": False},
            "observed_changed_files": ["src/arkx/cli.py", "tests/test_cli.py"],
            "steps": {
                "target_status_before": {"returncode": 0, "stdout": ""},
                "target_status_after": {"returncode": 0, "stdout": " M src/arkx/cli.py\n M tests/test_cli.py\n"},
                "target_head": {"returncode": 0, "stdout": "e401936979aea7f875508394aab1dac8f9e850d0\n"},
                "diff_check": {"returncode": 0},
            },
            "vertical_result": {
                "run_id": "m1-doctor-json-1-fixture",
                "status": "VERIFIED",
                "reason": "DECLARED_VERIFIER_PASSED",
                "changed_files": ["src/arkx/cli.py", "tests/test_cli.py"],
                "evidence_root": str(run_root),
            },
        })
        write(run_root / "request.json", {
            "request_id": "m1-doctor-json-1",
            "task_ref": "issue-57-doctor-json",
            "requested_scope": ["src/arkx/cli.py", "tests/test_cli.py"],
        })
        write(run_root / "authority-grant.json", {
            "request_id": "m1-doctor-json-1",
            "acceptance_authority_ref": "acceptance://independent-pending",
            "authorized_scope": ["src/arkx/cli.py", "tests/test_cli.py"],
            "max_commands": 1,
        })
        write(run_root / "execution.json", {
            "status": "EXECUTED",
            "reason": "EXECUTION_OBSERVED",
            "invocation_state": "OBSERVED",
            "command_result": {"timed_out": False, "environment_error": None, "exit_code": 0},
        })
        write(run_root / "changed-files.json", {"changed_files": ["src/arkx/cli.py", "tests/test_cli.py"]})
        write(run_root / "verification-summary.json", {
            "status": "PASSED", "returncode": 0, "error_kind": None, "evidence_ref": "evidence://verification"
        })
        write(run_root / "result.json", {
            "run_id": "m1-doctor-json-1-fixture", "status": "VERIFIED", "reason": "DECLARED_VERIFIER_PASSED"
        })
        write(run_root / "git-head.json", {
            "returncode": 0, "stdout": "e401936979aea7f875508394aab1dac8f9e850d0\n"
        })
        write(run_root / "git-status-before.json", {"returncode": 0, "stdout": ""})
        (run_root / "workspace.patch").write_text(
            'diff --git a/src/arkx/cli.py b/src/arkx/cli.py\n'
            '+doctor_parser.add_argument("--json", action="store_true", dest="as_json")\n'
            '+json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))\n'
            'diff --git a/tests/test_cli.py b/tests/test_cli.py\n'
            '+    def test_doctor_json_output_is_canonical(self):\n',
            encoding="utf-8",
        )
        write(run_root / "verification" / "m1-doctor-json-1-fixture" / "verification-a.json", {
            "run_id": "m1-doctor-json-1-fixture",
            "result": {"status": "PASSED", "exit_code": 0},
            "error_kind": None,
        })

    def test_accepts_complete_frozen_m1_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_bundle(root)
            decision = review_m1_doctor_json(root)
            self.assertEqual(decision.status, AcceptanceStatus.ACCEPTED)
            self.assertEqual(decision.authority_ref, M1_ACCEPTANCE_AUTHORITY)
            path = persist_acceptance(root, decision)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["decision"]["status"], "ACCEPTED")
            self.assertEqual(payload["promotion"], "NOT_AUTHORIZED")

    def test_blocks_when_summary_claims_provider_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_bundle(root)
            summary = json.loads((root / "m1-summary.json").read_text(encoding="utf-8"))
            summary["provider_called"] = True
            (root / "m1-summary.json").write_text(json.dumps(summary), encoding="utf-8")
            decision = review_m1_doctor_json(root)
            self.assertEqual(decision.status, AcceptanceStatus.BLOCKED)
            self.assertIn("provider_called=false", decision.rationale)

    def test_blocks_when_patch_does_not_contain_acceptance_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_bundle(root)
            run_root = root / "run-evidence" / "m1-doctor-json-1-fixture"
            (run_root / "workspace.patch").write_text("unrelated\n", encoding="utf-8")
            decision = review_m1_doctor_json(root)
            self.assertEqual(decision.status, AcceptanceStatus.BLOCKED)
            self.assertIn("doctor --json implementation present", decision.rationale)


if __name__ == "__main__":
    unittest.main()
