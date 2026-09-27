#!/usr/bin/env python3
"""Run Block 5.1-A: mini-SWE-agent v2.4.6 runtime-access qualification.

This gate proves only that an authorized Linux/Docker runtime can execute the
frozen mini-SWE-agent reference substrate prerequisites. It deliberately does
not execute no-op/gold controls, provider/model calls, benchmarks, or promotion.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MINI_REPO_URL = "https://github.com/SWE-agent/mini-swe-agent.git"
MINI_VERSION = "v2.4.6"
MINI_SHA = "a83fcae82d2a08f0ee0c688f9d137b3566c097f8"
MINI_CONFIG = "src/minisweagent/config/benchmarks/swebench.yaml"
MINI_CONFIG_BLOB = "106decd160e72e5164e29d15d23da354c29c309d"
DEFAULT_PROBE_IMAGE = "python:3.11-slim"


def run(argv: list[str], *, cwd: Path | None = None, timeout: int = 600) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    try:
        completed = subprocess.run(
            argv,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            check=False,
        )
        return {
            "argv": argv,
            "cwd": str(cwd) if cwd else None,
            "started_at": started,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "timeout": False,
            "error": None,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": argv,
            "cwd": str(cwd) if cwd else None,
            "started_at": started,
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timeout": True,
            "error": "TIMEOUT",
        }
    except OSError as exc:
        return {
            "argv": argv,
            "cwd": str(cwd) if cwd else None,
            "started_at": started,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "timeout": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def ok(result: dict[str, Any]) -> bool:
    return result.get("returncode") == 0 and not result.get("timeout")


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def fail(report: dict[str, Any], output: Path, classification: str) -> int:
    report["classification"] = classification
    write_report(output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe-image", default=DEFAULT_PROBE_IMAGE)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "logs" / "architecture" / "mini-v246-runtime-access" / "result.json",
    )
    args = parser.parse_args()

    output = args.output.expanduser().resolve()
    report: dict[str, Any] = {
        "schema_version": 1,
        "block": "5.1-A",
        "classification": "BLOCKED_RUNTIME_INFRASTRUCTURE",
        "reference": {
            "repository": MINI_REPO_URL,
            "version": MINI_VERSION,
            "commit": MINI_SHA,
            "config_path": MINI_CONFIG,
            "config_blob": MINI_CONFIG_BLOB,
        },
        "inputs": {"probe_image": args.probe_image},
        "steps": {},
        "no_op": "NOT_EXECUTED",
        "gold_oracle": "NOT_EXECUTED",
        "provider_model": "NOT_EXECUTED",
        "benchmark": "NOT_EXECUTED",
        "executor_promotion": "NOT_AUTHORIZED",
    }
    write_report(output, report)

    for tool in ("git", "docker"):
        path = shutil.which(tool)
        report["steps"][f"tool_{tool}"] = {
            "path": path,
            "status": "PASS" if path else "FAIL",
        }
        if not path:
            return fail(report, output, f"BLOCKED_{tool.upper()}_UNAVAILABLE")

    docker_info = run(["docker", "info", "--format", "{{json .}}"], timeout=60)
    report["steps"]["docker_info"] = docker_info
    if not ok(docker_info):
        return fail(report, output, "BLOCKED_DOCKER_DAEMON")

    with tempfile.TemporaryDirectory(prefix="codepro-mini-runtime-access-") as tmp:
        mini_repo = Path(tmp) / "mini-swe-agent"

        init = run(["git", "init", str(mini_repo)], timeout=60)
        report["steps"]["mini_git_init"] = init
        if not ok(init):
            return fail(report, output, "BLOCKED_REFERENCE_FETCH")

        remote = run(
            ["git", "-C", str(mini_repo), "remote", "add", "origin", MINI_REPO_URL],
            timeout=30,
        )
        report["steps"]["mini_remote"] = remote
        if not ok(remote):
            return fail(report, output, "BLOCKED_REFERENCE_FETCH")

        fetch = run(
            ["git", "-C", str(mini_repo), "fetch", "--depth", "1", "origin", MINI_SHA],
            timeout=600,
        )
        report["steps"]["mini_fetch"] = fetch
        if not ok(fetch):
            return fail(report, output, "BLOCKED_REFERENCE_FETCH")

        checkout = run(
            ["git", "-C", str(mini_repo), "checkout", "--detach", "FETCH_HEAD"],
            timeout=60,
        )
        report["steps"]["mini_checkout"] = checkout
        if not ok(checkout):
            return fail(report, output, "BLOCKED_REFERENCE_IDENTITY")

        head = run(["git", "-C", str(mini_repo), "rev-parse", "HEAD"], timeout=30)
        blob = run(
            ["git", "-C", str(mini_repo), "rev-parse", f"HEAD:{MINI_CONFIG}"],
            timeout=30,
        )
        clean = run(
            ["git", "-C", str(mini_repo), "status", "--porcelain"],
            timeout=30,
        )
        report["steps"]["mini_head"] = head
        report["steps"]["mini_config_blob"] = blob
        report["steps"]["mini_worktree"] = clean

        identity_ok = (
            ok(head)
            and ok(blob)
            and ok(clean)
            and head["stdout"].strip() == MINI_SHA
            and blob["stdout"].strip() == MINI_CONFIG_BLOB
            and not clean["stdout"].strip()
        )
        if not identity_ok:
            return fail(report, output, "BLOCKED_REFERENCE_IDENTITY")

        pull = run(["docker", "pull", args.probe_image], timeout=900)
        report["steps"]["docker_pull_probe_image"] = pull
        if not ok(pull):
            return fail(report, output, "BLOCKED_PROBE_IMAGE")

        image_id = run(
            ["docker", "image", "inspect", args.probe_image, "--format", "{{json .Id}}"],
            timeout=60,
        )
        repo_digests = run(
            ["docker", "image", "inspect", args.probe_image, "--format", "{{json .RepoDigests}}"],
            timeout=60,
        )
        image_os = run(
            ["docker", "image", "inspect", args.probe_image, "--format", "{{.Os}}"],
            timeout=60,
        )
        report["steps"]["probe_image_id"] = image_id
        report["steps"]["probe_image_repo_digests"] = repo_digests
        report["steps"]["probe_image_os"] = image_os
        if not (ok(image_id) and ok(repo_digests) and ok(image_os)):
            return fail(report, output, "BLOCKED_PROBE_IMAGE_IDENTITY")
        if image_os["stdout"].strip() != "linux":
            return fail(report, output, "BLOCKED_NON_LINUX_SUBSTRATE")

        probe = run(
            [
                "docker",
                "run",
                "--rm",
                "--workdir",
                "/testbed",
                args.probe_image,
                "bash",
                "-c",
                (
                    'set -e; '
                    'test "$(uname -s)" = Linux; '
                    'test -d /testbed; '
                    'test "$(pwd)" = /testbed; '
                    'printf "runtime-access-ready\\n"'
                ),
            ],
            timeout=180,
        )
        report["steps"]["container_probe"] = probe
        if not ok(probe) or "runtime-access-ready" not in probe["stdout"].splitlines():
            return fail(report, output, "BLOCKED_DOCKER_LINUX_SUBSTRATE")

        report["runtime"] = {
            "docker_daemon_access": "PASS",
            "linux_substrate": "PASS",
            "cwd": "/testbed",
            "bash_c": "PASS",
            "probe_image": args.probe_image,
            "image_id": json.loads(image_id["stdout"]),
            "repo_digests": json.loads(repo_digests["stdout"]),
        }

    report["classification"] = "RUNTIME_ACCESS_READY"
    write_report(output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
