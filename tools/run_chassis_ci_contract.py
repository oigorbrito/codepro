from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def _run(argv: list[str], cwd: Path, timeout: float) -> dict[str, Any]:
    started = time.time()
    try:
        cp = subprocess.run(
            argv,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            shell=False,
        )
        return {
            "argv": argv,
            "exit_code": cp.returncode,
            "stdout": cp.stdout,
            "stderr": cp.stderr,
            "timed_out": False,
            "launch_error": None,
            "wall_seconds": round(time.time() - started, 6),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": argv,
            "exit_code": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timed_out": True,
            "launch_error": None,
            "wall_seconds": round(time.time() - started, 6),
        }
    except OSError as exc:
        return {
            "argv": argv,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "timed_out": False,
            "launch_error": f"{type(exc).__name__}: {exc}",
            "wall_seconds": round(time.time() - started, 6),
        }


def _runner_identity() -> dict[str, Any]:
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": sys.version,
        "github_runner_os": os.getenv("RUNNER_OS"),
        "github_runner_arch": os.getenv("RUNNER_ARCH"),
        "github_image_os": os.getenv("ImageOS"),
        "github_image_version": os.getenv("ImageVersion"),
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
        "github_sha": os.getenv("GITHUB_SHA"),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--candidate", required=True)
    p.add_argument("--candidate-revision", required=True)
    p.add_argument("--candidate-command-json", required=True)
    p.add_argument("--verifier-command-json", required=True)
    p.add_argument("--workdir", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--timeout-seconds", type=float, default=60.0)
    args = p.parse_args()

    candidate_argv = json.loads(args.candidate_command_json)
    verifier_argv = json.loads(args.verifier_command_json)
    if not isinstance(candidate_argv, list) or not all(isinstance(x, str) for x in candidate_argv):
        raise SystemExit("candidate command must be a JSON string array")
    if not isinstance(verifier_argv, list) or not all(isinstance(x, str) for x in verifier_argv):
        raise SystemExit("verifier command must be a JSON string array")

    workdir = Path(args.workdir).resolve()
    out = Path(args.output)
    workdir.mkdir(parents=True, exist_ok=True)
    out.parent.mkdir(parents=True, exist_ok=True)

    candidate = _run(candidate_argv, workdir, args.timeout_seconds)
    verifier = _run(verifier_argv, workdir, args.timeout_seconds)

    infra_failure = any([
        candidate["launch_error"] is not None,
        candidate["timed_out"],
        verifier["launch_error"] is not None,
        verifier["timed_out"],
    ])

    if infra_failure:
        classification = "INFRA_FAILURE"
        verifier_result = "UNKNOWN"
        rc = 3
    elif verifier["exit_code"] == 0:
        classification = "VERIFIED_PASS"
        verifier_result = "PASS"
        rc = 0
    else:
        classification = "VERIFIED_FAIL"
        verifier_result = "FAIL"
        rc = 2

    record = {
        "schema_version": 1,
        "candidate": args.candidate,
        "candidate_revision": args.candidate_revision,
        "project_commit": os.getenv("GITHUB_SHA"),
        "runner_identity": _runner_identity(),
        "timeout_seconds": args.timeout_seconds,
        "candidate_observation": candidate,
        "verifier_observation": verifier,
        "verifier_result": verifier_result,
        "classification": classification,
        "invariants": {
            "shell_interpretation": False,
            "candidate_exit_is_task_success": False,
            "verifier_is_independent": True,
            "silent_fallback": False,
        },
    }
    out.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "candidate": args.candidate,
        "classification": classification,
        "verifier_result": verifier_result,
        "output": str(out),
    }, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
