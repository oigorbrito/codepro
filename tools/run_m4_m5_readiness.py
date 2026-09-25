#!/usr/bin/env python3
"""Validate MVP M4 private install/use and M5 release-candidate readiness locally."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).parents[1].resolve()
REPOSITORY = "https://github.com/oigorbrito/codepro.git"


def run(
    argv: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 300,
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


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repo_head(root: Path) -> str:
    result = run(["git", "rev-parse", "HEAD"], cwd=root)
    if result["returncode"] != 0:
        raise RuntimeError("unable to resolve candidate HEAD")
    return result["stdout"].strip()


def create_target_repo(root: Path) -> str:
    root.mkdir(parents=True)
    for argv in (
        ["git", "init"],
        ["git", "config", "user.email", "m4@example.invalid"],
        ["git", "config", "user.name", "CodePro M4"],
    ):
        result = run(argv, cwd=root)
        if result["returncode"] != 0:
            raise RuntimeError(f"target repo setup failed: {result}")
    (root / "src").mkdir()
    (root / "src" / "value.txt").write_text("before\n", encoding="utf-8")
    for argv in (["git", "add", "."], ["git", "commit", "-m", "base"]):
        result = run(argv, cwd=root)
        if result["returncode"] != 0:
            raise RuntimeError(f"target repo commit failed: {result}")
    return repo_head(root)


def finish(report: dict[str, Any], path: Path, code: int) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(rendered, encoding="utf-8", newline="\n")
    sys.stdout.write(rendered)
    return code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", required=True, type=Path)
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument("--m1-evidence-root", required=True, type=Path)
    parser.add_argument("--m2-m3-evidence-root", required=True, type=Path)
    args = parser.parse_args()

    work = args.work_root.expanduser().resolve()
    evidence = args.evidence_root.expanduser().resolve()
    m1_root = args.m1_evidence_root.expanduser().resolve()
    m23_root = args.m2_m3_evidence_root.expanduser().resolve()
    summary = evidence / "m4-m5-readiness-summary.json"

    report: dict[str, Any] = {
        "schema_version": 1,
        "classification": "BLOCKED",
        "candidate_sha": None,
        "provider_called": False,
        "model_called": False,
        "executor_promotion": "NOT_AUTHORIZED",
        "release": "NOT_AUTHORIZED",
        "publication": "NOT_AUTHORIZED",
        "activation": "NOT_AUTHORIZED",
        "m4": {},
        "m5": {},
    }

    if not ((3, 12) <= sys.version_info[:2] <= (3, 14)):
        report["classification"] = "BLOCKED_UNSUPPORTED_PYTHON"
        return finish(report, summary, 2)
    if work.exists() or (evidence.exists() and any(evidence.iterdir())):
        report["classification"] = "BLOCKED_ROOT_NOT_FRESH"
        return finish(report, summary, 2)

    try:
        candidate_sha = repo_head(ROOT)
    except RuntimeError as exc:
        report["classification"] = "BLOCKED_CANDIDATE_IDENTITY"
        report["error"] = str(exc)
        return finish(report, summary, 2)
    report["candidate_sha"] = candidate_sha

    m1_acceptance = m1_root / "acceptance.json"
    m23_summary = m23_root / "m2-m3-summary.json"
    if not m1_acceptance.is_file() or not m23_summary.is_file():
        report["classification"] = "BLOCKED_PRIOR_EVIDENCE_MISSING"
        return finish(report, summary, 2)

    try:
        m1_payload = json.loads(m1_acceptance.read_text(encoding="utf-8"))
        m23_payload = json.loads(m23_summary.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report["classification"] = "BLOCKED_PRIOR_EVIDENCE_INVALID"
        report["error"] = f"{type(exc).__name__}: {exc}"
        return finish(report, summary, 2)

    report["m5"]["prior_evidence"] = {
        "m1_acceptance_sha256": file_sha256(m1_acceptance),
        "m1_status": (m1_payload.get("decision") or {}).get("status"),
        "m2_m3_summary_sha256": file_sha256(m23_summary),
        "m2_m3_classification": m23_payload.get("classification"),
    }
    if (
        report["m5"]["prior_evidence"]["m1_status"] != "ACCEPTED"
        or report["m5"]["prior_evidence"]["m2_m3_classification"] != "M2_M3_VALIDATED"
    ):
        report["classification"] = "BLOCKED_PRIOR_GATES"
        return finish(report, summary, 2)

    work.mkdir(parents=True)
    evidence.mkdir(parents=True, exist_ok=True)
    candidate = work / "candidate"
    clone = run(["git", "clone", "--no-checkout", REPOSITORY, str(candidate)], timeout=240)
    report["m5"]["candidate_clone"] = clone
    if clone["returncode"] != 0:
        report["classification"] = "BLOCKED_CANDIDATE_CLONE"
        return finish(report, summary, 2)

    fetch = run(["git", "fetch", "--depth", "1", "origin", candidate_sha], cwd=candidate)
    checkout = run(["git", "checkout", "--detach", candidate_sha], cwd=candidate)
    head = run(["git", "rev-parse", "HEAD"], cwd=candidate)
    status = run(["git", "status", "--porcelain"], cwd=candidate)
    report["m5"]["candidate_identity"] = {
        "fetch": fetch,
        "checkout": checkout,
        "head": head,
        "status": status,
    }
    if (
        fetch["returncode"] != 0
        or checkout["returncode"] != 0
        or head["returncode"] != 0
        or head["stdout"].strip() != candidate_sha
        or status["returncode"] != 0
        or status["stdout"].strip()
    ):
        report["classification"] = "BLOCKED_CANDIDATE_IDENTITY"
        return finish(report, summary, 2)

    venv = work / "venv"
    create_venv = run([sys.executable, "-m", "venv", str(venv)], timeout=180)
    report["m4"]["create_venv"] = create_venv
    if create_venv["returncode"] != 0:
        report["classification"] = "BLOCKED_PRIVATE_ENVIRONMENT"
        return finish(report, summary, 2)

    vpython = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    codepro = venv / ("Scripts/codepro.exe" if os.name == "nt" else "bin/codepro")
    install = run(
        [
            str(vpython),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-input",
            "--no-deps",
            str(candidate),
        ],
        timeout=300,
    )
    report["m4"]["install"] = install
    if install["returncode"] != 0:
        report["classification"] = "BLOCKED_PRIVATE_INSTALL"
        return finish(report, summary, 2)

    package = run([str(vpython), "-m", "pip", "show", "codepro"])
    version = run([str(codepro), "--version"])
    doctor = run([str(codepro), "doctor"])
    inspect = run([str(codepro), "inspect", str(candidate), "--json"])
    module_help = run([str(vpython), "-m", "arkx", "--help"])
    report["m4"]["installed_cli"] = {
        "pip_show": package,
        "version": version,
        "doctor": doctor,
        "inspect": inspect,
        "module_help": module_help,
    }
    if any(x["returncode"] != 0 for x in (package, version, doctor, inspect, module_help)):
        report["classification"] = "BLOCKED_INSTALLED_CLI"
        return finish(report, summary, 2)

    target = work / "authorized-target"
    try:
        target_revision = create_target_repo(target)
    except RuntimeError as exc:
        report["classification"] = "BLOCKED_M4_TARGET_SETUP"
        report["error"] = str(exc)
        return finish(report, summary, 2)

    executor_code = (
        "from pathlib import Path;"
        "Path('src/value.txt').write_text('after\\n', encoding='utf-8')"
    )
    verifier_code = (
        "from pathlib import Path;"
        "raise SystemExit(0 if Path('src/value.txt').read_text(encoding='utf-8') == 'after\\n' else 1)"
    )
    vertical = run(
        [
            str(codepro),
            "run",
            "--workspace", str(target),
            "--revision", target_revision,
            "--request-id", "m4-private-use-1",
            "--task-id", "m4-private-installed-cli",
            "--requester", "user://authorized-private-m4",
            "--authority", "authority://m4-private",
            "--acceptance-authority", "acceptance://m4-pending",
            "--scope", "src",
            "--candidate-file", "src/value.txt",
            "--affected-component", "src",
            "--characterization-source-ref", "evidence://m4-private-use-task",
            "--max-wall-time", "30",
            "--attempt-id", "m4-attempt-1",
            "--evidence-dir", str(evidence / "m4-run-evidence"),
            "--verifier-argv-json", json.dumps([str(vpython), "-c", verifier_code]),
            "--",
            str(vpython), "-c", executor_code,
        ],
        cwd=work,
        timeout=120,
    )
    report["m4"]["installed_vertical"] = vertical
    if vertical["returncode"] != 0:
        report["classification"] = "BLOCKED_M4_PRIVATE_USE"
        return finish(report, summary, 2)
    try:
        vertical_payload = json.loads(vertical["stdout"])
    except json.JSONDecodeError:
        report["classification"] = "BLOCKED_M4_PRIVATE_USE_PARSE"
        return finish(report, summary, 2)
    report["m4"]["installed_vertical_result"] = vertical_payload
    if vertical_payload.get("status") != "VERIFIED":
        report["classification"] = "BLOCKED_M4_PRIVATE_USE"
        return finish(report, summary, 2)

    source_env = os.environ.copy()
    source_env["PYTHONPATH"] = str(candidate / "src")
    checks = {
        "foundation": run([str(vpython), "tools/check_foundation.py"], cwd=candidate, env=source_env),
        "baseline": run([str(vpython), "-m", "arkx.baseline"], cwd=candidate, env=source_env),
        "full_suite": run(
            [str(vpython), "-m", "unittest", "discover", "-s", "tests", "-t", ".", "-v"],
            cwd=candidate,
            env=source_env,
            timeout=600,
        ),
        "mutation_probe": run([str(vpython), "tools/mutation_probe.py"], cwd=candidate, env=source_env),
        "fingerprint": run([str(vpython), "tools/chassis_fingerprint.py"], cwd=candidate, env=source_env),
        "compileall": run(
            [str(vpython), "-m", "compileall", "-q", "src", "tests", "tools"],
            cwd=candidate,
            env=source_env,
            timeout=300,
        ),
    }
    report["m5"]["candidate_checks"] = checks
    failed = [name for name, result in checks.items() if result["returncode"] != 0]
    if failed:
        report["classification"] = "BLOCKED_M5_CANDIDATE_CHECKS"
        report["m5"]["failed_checks"] = failed
        return finish(report, summary, 2)

    report["m4"]["classification"] = "M4_PRIVATE_INSTALL_AND_USE_VALIDATED"
    report["m5"]["classification"] = "M5_RELEASE_CANDIDATE_READY_FOR_INDEPENDENT_REVIEW"
    report["classification"] = "M4_M5_READINESS_VALIDATED"
    return finish(report, summary, 0)


if __name__ == "__main__":
    raise SystemExit(main())
