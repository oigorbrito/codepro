#!/usr/bin/env python3
"""Validate MVP M2 negative outcomes and M3 controlled repetition."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).parents[1].resolve()
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def proc(argv: list[str], *, cwd: Path | None = None, timeout: int = 240, env=None) -> dict[str, Any]:
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


def init_repo(root: Path) -> str:
    root.mkdir()
    for argv in (
        ["git", "init"],
        ["git", "config", "user.email", "m2@example.invalid"],
        ["git", "config", "user.name", "CodePro M2"],
    ):
        result = proc(argv, cwd=root)
        if result["returncode"] != 0:
            raise RuntimeError(result)
    (root / "src").mkdir()
    (root / "src" / "value.txt").write_text("base\n", encoding="utf-8")
    for argv in (["git", "add", "."], ["git", "commit", "-m", "base"]):
        result = proc(argv, cwd=root)
        if result["returncode"] != 0:
            raise RuntimeError(result)
    return proc(["git", "rev-parse", "HEAD"], cwd=root)["stdout"].strip()


def negative_case(
    *,
    root: Path,
    revision: str,
    evidence: Path,
    request_id: str,
    attempt_id: str,
    executor_argv: tuple[str, ...],
    timeout_seconds: float,
):
    from arkx.vertical import run_vertical
    return run_vertical(
        workspace=root,
        revision=revision,
        request_id=request_id,
        task_id=request_id,
        requester_ref="user://m2-validation",
        authority_ref="authority://m2-validation",
        acceptance_authority_ref="acceptance://m2-validation",
        scope=("src",),
        executor_argv=executor_argv,
        verifier_argv=(sys.executable, "-c", "raise SystemExit(0)"),
        evidence_dir=evidence,
        max_wall_time_seconds=timeout_seconds,
        attempt_id=attempt_id,
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", required=True, type=Path)
    parser.add_argument("--evidence-root", required=True, type=Path)
    args = parser.parse_args()
    work = args.work_root.expanduser().resolve()
    evidence = args.evidence_root.expanduser().resolve()
    summary_path = evidence / "m2-m3-summary.json"

    report: dict[str, Any] = {
        "schema_version": 1,
        "classification": "BLOCKED",
        "provider_called": False,
        "model_called": False,
        "promotion": "NOT_AUTHORIZED",
        "release": "NOT_AUTHORIZED",
        "m2": {},
        "m3": {},
    }

    if work.exists() or (evidence.exists() and any(evidence.iterdir())):
        report["classification"] = "BLOCKED_ROOT_NOT_FRESH"
        return finish(report, summary_path, 2)
    work.mkdir(parents=True)
    evidence.mkdir(parents=True, exist_ok=True)

    tests_env = os.environ.copy()
    tests_env["PYTHONPATH"] = str(SRC)
    focused = proc(
        [sys.executable, "-m", "unittest", "-v", "tests.test_vertical", "tests.test_cli"],
        cwd=ROOT,
        env=tests_env,
    )
    report["focused_tests"] = focused
    if focused["returncode"] != 0:
        report["classification"] = "BLOCKED_M2_M3_CONTRACT_TESTS"
        return finish(report, summary_path, 2)

    with tempfile.TemporaryDirectory(prefix="codepro-m2-") as tmp:
        base = Path(tmp)
        cases = {}

        failure_repo = base / "failure"
        rev = init_repo(failure_repo)
        cases["failure"] = negative_case(
            root=failure_repo,
            revision=rev,
            evidence=evidence / "m2-failure",
            request_id="m2-failure",
            attempt_id="attempt-failure",
            executor_argv=(sys.executable, "-c", "raise SystemExit(9)"),
            timeout_seconds=10,
        ).to_dict()

        timeout_repo = base / "timeout"
        rev = init_repo(timeout_repo)
        cases["timeout"] = negative_case(
            root=timeout_repo,
            revision=rev,
            evidence=evidence / "m2-timeout",
            request_id="m2-timeout",
            attempt_id="attempt-timeout",
            executor_argv=(sys.executable, "-c", "import time; time.sleep(2)"),
            timeout_seconds=0.1,
        ).to_dict()

        env_repo = base / "environment"
        rev = init_repo(env_repo)
        cases["environment_unavailable"] = negative_case(
            root=env_repo,
            revision=rev,
            evidence=evidence / "m2-environment",
            request_id="m2-environment",
            attempt_id="attempt-environment",
            executor_argv=("codepro-missing-executable-6d9c0b",),
            timeout_seconds=10,
        ).to_dict()

        report["m2"] = cases
        expected = {
            "failure": "FAILED",
            "timeout": "TIMED_OUT",
            "environment_unavailable": "ENVIRONMENT_UNAVAILABLE",
        }
        if any(cases[name]["status"] != state for name, state in expected.items()):
            report["classification"] = "BLOCKED_M2_FALSE_STATE"
            return finish(report, summary_path, 2)

    m3_runs = []
    for index in (1, 2):
        target = work / f"repeat-{index}"
        ev = evidence / f"m3-repeat-{index}"
        argv = [
            sys.executable,
            str(ROOT / "tools" / "run_m1_doctor_json.py"),
            "--target-workspace", str(target),
            "--evidence-root", str(ev),
            "--attempt-id", f"m3-attempt-{index}",
        ]
        result = proc(argv, cwd=ROOT, timeout=300)
        entry: dict[str, Any] = {"process": result}
        if result["returncode"] != 0:
            report["m3"]["runs"] = m3_runs + [entry]
            report["classification"] = "BLOCKED_M3_REPEAT_EXECUTION"
            return finish(report, summary_path, 2)
        payload = json.loads(result["stdout"])
        entry["summary"] = payload
        vertical = payload["vertical_result"]
        patch = Path(vertical["evidence_root"]) / "workspace.patch"
        entry["patch_sha256"] = sha256(patch)
        m3_runs.append(entry)

    report["m3"]["runs"] = m3_runs
    first, second = (item["summary"] for item in m3_runs)
    first_v, second_v = first["vertical_result"], second["vertical_result"]
    report["m3"]["comparison"] = {
        "same_base_sha": first["target_base_sha"] == second["target_base_sha"],
        "same_task_id": first["task_id"] == second["task_id"],
        "same_changed_files": first["observed_changed_files"] == second["observed_changed_files"],
        "same_patch_sha256": m3_runs[0]["patch_sha256"] == m3_runs[1]["patch_sha256"],
        "distinct_attempt_id": first["attempt_id"] != second["attempt_id"],
        "distinct_run_id": first_v["run_id"] != second_v["run_id"],
        "both_verified": first_v["status"] == second_v["status"] == "VERIFIED",
    }
    if not all(report["m3"]["comparison"].values()):
        report["classification"] = "BLOCKED_M3_COMPARISON"
        return finish(report, summary_path, 2)

    report["classification"] = "M2_M3_VALIDATED"
    return finish(report, summary_path, 0)


def finish(report: dict[str, Any], path: Path, code: int) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(rendered, encoding="utf-8", newline="\n")
    sys.stdout.write(rendered)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
