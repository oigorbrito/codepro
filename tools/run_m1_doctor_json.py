#!/usr/bin/env python3
"""Execute the frozen first real CodePro M1 task against an exact repository revision."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).parents[1].resolve()
SRC = ROOT / "src"
TARGET_REPOSITORY = "https://github.com/oigorbrito/codepro.git"
TARGET_BASE_SHA = "e401936979aea7f875508394aab1dac8f9e850d0"
TASK_REF = "github://oigorbrito/codepro/issues/57"
REQUEST_ID = "m1-doctor-json-1"
TASK_ID = "issue-57-doctor-json"


def run(
    argv: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 180,
) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            argv,
            cwd=None if cwd is None else str(cwd),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            check=False,
            timeout=timeout,
        )
        return {
            "argv": argv,
            "cwd": None if cwd is None else str(cwd),
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "timeout": False,
            "error": None,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": argv,
            "cwd": None if cwd is None else str(cwd),
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timeout": True,
            "error": "TIMEOUT",
        }
    except OSError as exc:
        return {
            "argv": argv,
            "cwd": None if cwd is None else str(cwd),
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "timeout": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def executor_script() -> str:
    return r'''
from pathlib import Path

cli = Path("src/arkx/cli.py")
text = cli.read_text(encoding="utf-8")

old = """    subparsers.add_parser(
        "doctor",
        help="Check whether the local Python runtime can execute the current chassis.",
        description="Check the local runtime and core package import boundary.",
    )
"""
new = """    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Check whether the local Python runtime can execute the current chassis.",
        description="Check the local runtime and core package import boundary.",
    )
    doctor_parser.add_argument("--json", action="store_true", dest="as_json")
"""
if old not in text:
    raise SystemExit("doctor parser anchor not found")
text = text.replace(old, new, 1)

old = """def _doctor() -> int:
    version = sys.version_info[:2]
    supported = _SUPPORTED_MIN <= version <= _SUPPORTED_MAX

    checks = (
        ("python", supported, platform.python_version()),
        ("core", True, "importable"),
    )
    for name, ok, detail in checks:
        state = "PASS" if ok else "FAIL"
        print(f"{name}: {state} ({detail})")

    overall = all(ok for _, ok, _ in checks)
    print(f"status: {'PASS' if overall else 'FAIL'}")
    return 0 if overall else 1
"""
new = """def _doctor(*, as_json: bool = False) -> int:
    version = sys.version_info[:2]
    supported = _SUPPORTED_MIN <= version <= _SUPPORTED_MAX

    checks = (
        ("python", supported, platform.python_version()),
        ("core", True, "importable"),
    )
    overall = all(ok for _, ok, _ in checks)

    if as_json:
        payload = {
            "checks": [
                {"name": name, "status": "PASS" if ok else "FAIL", "detail": detail}
                for name, ok, detail in checks
            ],
            "status": "PASS" if overall else "FAIL",
        }
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0 if overall else 1

    for name, ok, detail in checks:
        state = "PASS" if ok else "FAIL"
        print(f"{name}: {state} ({detail})")
    print(f"status: {'PASS' if overall else 'FAIL'}")
    return 0 if overall else 1
"""
if old not in text:
    raise SystemExit("doctor function anchor not found")
text = text.replace(old, new, 1)

old = """    if args.command == "doctor":
        return _doctor()
"""
new = """    if args.command == "doctor":
        return _doctor(as_json=args.as_json)
"""
if old not in text:
    raise SystemExit("doctor dispatch anchor not found")
text = text.replace(old, new, 1)
cli.write_text(text, encoding="utf-8", newline="\n")

tests = Path("tests/test_cli.py")
text = tests.read_text(encoding="utf-8")
anchor = """    def test_inspect_text_output_is_read_only_and_explicit(self):
"""
method = """    def test_doctor_json_output_is_canonical(self):
        code, output = self.capture(["doctor", "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(output)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(
            [item["name"] for item in payload["checks"]],
            ["python", "core"],
        )
        self.assertEqual(
            output.strip(),
            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )

"""
if anchor not in text:
    raise SystemExit("test insertion anchor not found")
text = text.replace(anchor, method + anchor, 1)
tests.write_text(text, encoding="utf-8", newline="\n")
'''


def verifier_code() -> str:
    return (
        "import pathlib,sys,unittest;"
        "sys.path.insert(0,str(pathlib.Path('src').resolve()));"
        "suite=unittest.defaultTestLoader.loadTestsFromName('tests.test_cli');"
        "result=unittest.TextTestRunner(verbosity=2).run(suite);"
        "raise SystemExit(0 if result.wasSuccessful() else 1)"
    )


def finish(report: dict[str, Any], output: Path, code: int) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    output.write_text(rendered, encoding="utf-8", newline="\n")
    sys.stdout.write(rendered)
    return code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-workspace", required=True, type=Path)
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument("--attempt-id", default="attempt-1")
    args = parser.parse_args()

    target = args.target_workspace.expanduser().resolve()
    evidence = args.evidence_root.expanduser().resolve()
    summary = evidence / "m1-summary.json"

    report: dict[str, Any] = {
        "schema_version": 1,
        "classification": "BLOCKED",
        "task_ref": TASK_REF,
        "request_id": REQUEST_ID,
        "task_id": TASK_ID,
        "target_repository": TARGET_REPOSITORY,
        "target_base_sha": TARGET_BASE_SHA,
        "target_workspace": str(target),
        "evidence_root": str(evidence),
        "attempt_id": args.attempt_id,
        "provider_called": False,
        "model_called": False,
        "executor": {
            "id": "local-command",
            "selection": "EXPLICIT",
            "fallback_allowed": False,
        },
        "promotion": "NOT_AUTHORIZED",
        "acceptance": "NOT_EXECUTED",
        "steps": {},
    }

    if not ((3, 12) <= sys.version_info[:2] <= (3, 14)):
        report["classification"] = "BLOCKED_UNSUPPORTED_PYTHON"
        return finish(report, summary, 2)

    if target.exists():
        report["classification"] = "BLOCKED_TARGET_ALREADY_EXISTS"
        return finish(report, summary, 2)
    if evidence.exists() and any(evidence.iterdir()):
        report["classification"] = "BLOCKED_EVIDENCE_ROOT_NOT_EMPTY"
        return finish(report, summary, 2)
    evidence.mkdir(parents=True, exist_ok=True)

    clone = run(["git", "clone", "--no-checkout", TARGET_REPOSITORY, str(target)], timeout=180)
    report["steps"]["clone"] = clone
    if clone["returncode"] != 0:
        report["classification"] = "BLOCKED_TARGET_CLONE"
        return finish(report, summary, 2)

    fetch = run(["git", "fetch", "--depth", "1", "origin", TARGET_BASE_SHA], cwd=target)
    report["steps"]["fetch_base"] = fetch
    if fetch["returncode"] != 0:
        report["classification"] = "BLOCKED_TARGET_BASE_FETCH"
        return finish(report, summary, 2)

    checkout = run(["git", "checkout", "--detach", TARGET_BASE_SHA], cwd=target)
    report["steps"]["checkout_base"] = checkout
    if checkout["returncode"] != 0:
        report["classification"] = "BLOCKED_TARGET_BASE_CHECKOUT"
        return finish(report, summary, 2)

    head = run(["git", "rev-parse", "HEAD"], cwd=target)
    status = run(["git", "status", "--porcelain"], cwd=target)
    report["steps"]["target_head"] = head
    report["steps"]["target_status_before"] = status
    if (
        head["returncode"] != 0
        or head["stdout"].strip() != TARGET_BASE_SHA
        or status["returncode"] != 0
        or status["stdout"].strip()
    ):
        report["classification"] = "BLOCKED_TARGET_IDENTITY"
        return finish(report, summary, 2)

    verifier_argv = [sys.executable, "-c", verifier_code()]
    command = [
        sys.executable,
        "-m",
        "arkx",
        "run",
        "--workspace",
        str(target),
        "--revision",
        TARGET_BASE_SHA,
        "--request-id",
        REQUEST_ID,
        "--task-id",
        TASK_ID,
        "--requester",
        "user://authorized-local-m1",
        "--authority",
        "authority://m1-local",
        "--acceptance-authority",
        "acceptance://independent-pending",
        "--scope",
        "src/arkx/cli.py",
        "--scope",
        "tests/test_cli.py",
        "--candidate-file",
        "src/arkx/cli.py",
        "--candidate-file",
        "tests/test_cli.py",
        "--affected-component",
        "cli",
        "--max-wall-time",
        "120",
        "--attempt-id",
        args.attempt_id,
        "--evidence-dir",
        str(evidence / "run-evidence"),
        "--verifier-argv-json",
        json.dumps(verifier_argv),
        "--",
        sys.executable,
        "-c",
        executor_script(),
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC)
    execution = run(command, cwd=ROOT, env=env, timeout=240)
    report["steps"]["codepro_run"] = execution
    if execution["returncode"] != 0:
        report["classification"] = "BLOCKED_M1_EXECUTION"
        return finish(report, summary, 2)

    try:
        vertical_result = json.loads(execution["stdout"])
    except json.JSONDecodeError:
        report["classification"] = "BLOCKED_M1_RESULT_PARSE"
        return finish(report, summary, 2)
    report["vertical_result"] = vertical_result
    if vertical_result.get("status") != "VERIFIED":
        report["classification"] = "BLOCKED_M1_NOT_VERIFIED"
        return finish(report, summary, 2)

    final_status = run(["git", "status", "--porcelain=v1"], cwd=target)
    diff = run(["git", "diff", "--check"], cwd=target)
    report["steps"]["target_status_after"] = final_status
    report["steps"]["diff_check"] = diff
    if diff["returncode"] != 0:
        report["classification"] = "BLOCKED_M1_DIFF_CHECK"
        return finish(report, summary, 2)

    changed = []
    for line in final_status["stdout"].splitlines():
        if len(line) >= 4:
            changed.append(line[3:].replace("\\", "/"))
    expected = {"src/arkx/cli.py", "tests/test_cli.py"}
    if set(changed) != expected:
        report["classification"] = "BLOCKED_M1_SCOPE_POSTCHECK"
        report["observed_changed_files"] = sorted(changed)
        return finish(report, summary, 2)

    report["observed_changed_files"] = sorted(changed)
    report["classification"] = "M1_REAL_VERTICAL_VERIFIED"
    report["acceptance"] = "PENDING_INDEPENDENT_ACCEPTANCE"
    return finish(report, summary, 0)


if __name__ == "__main__":
    raise SystemExit(main())
