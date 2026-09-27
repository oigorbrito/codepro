#!/usr/bin/env python3
"""Provider-free preflight for the benchmark-faithful mini-SWE-agent substrate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

PINNED_MINI_COMMIT = "a83fcae82d2a08f0ee0c688f9d137b3566c097f8"
PINNED_CONFIG_BLOB_SHA = "106decd160e72e5164e29d15d23da354c29c309d"
BUNDLED_CONFIG = Path("src/minisweagent/config/benchmarks/swebench.yaml")


def _run(argv: list[str], *, cwd: Path | None = None, timeout: int = 30) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            argv,
            cwd=str(cwd) if cwd is not None else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            check=False,
        )
        return {
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "timeout": False,
            "error": None,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": argv,
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timeout": True,
            "error": "TIMEOUT",
        }
    except OSError as exc:
        return {
            "argv": argv,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "timeout": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _check_config(mini_repo: Path) -> dict[str, Any]:
    path = mini_repo / BUNDLED_CONFIG
    if not path.is_file():
        return {"status": "FAIL", "reason": "PINNED_CONFIG_MISSING", "path": str(path)}

    text = path.read_text(encoding="utf-8")
    blob = _run(["git", "rev-parse", f"HEAD:{BUNDLED_CONFIG.as_posix()}"], cwd=mini_repo)
    blob_sha = blob["stdout"].strip() if blob["returncode"] == 0 else None
    required_fragments = (
        'cwd: "/testbed"',
        'interpreter: ["bash", "-c"]',
        "BASH_ENV: /root/.bashrc",
        "environment_class: docker",
    )
    missing = [fragment for fragment in required_fragments if fragment not in text]
    ok = blob_sha == PINNED_CONFIG_BLOB_SHA and not missing
    return {
        "status": "PASS" if ok else "FAIL",
        "reason": None if ok else "PINNED_CONFIG_DRIFT",
        "path": str(path),
        "git_blob_sha": blob_sha,
        "expected_git_blob_sha": PINNED_CONFIG_BLOB_SHA,
        "git_blob_lookup": blob,
        "missing_required_fragments": missing,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mini-repo", required=True, type=Path)
    parser.add_argument(
        "--probe-image",
        help="Optional already-available Linux image to execute with docker run --rm.",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    mini_repo = args.mini_repo.expanduser().resolve()
    report: dict[str, Any] = {
        "schema_version": 1,
        "classification": "BLOCKED",
        "provider_called": False,
        "expected_mini_commit": PINNED_MINI_COMMIT,
        "checks": {},
    }

    head = _run(["git", "rev-parse", "HEAD"], cwd=mini_repo)
    actual_head = head["stdout"].strip() if head["returncode"] == 0 else None
    report["checks"]["mini_commit"] = {
        **head,
        "actual": actual_head,
        "expected": PINNED_MINI_COMMIT,
        "status": "PASS" if actual_head == PINNED_MINI_COMMIT else "FAIL",
    }

    status = _run(["git", "status", "--porcelain"], cwd=mini_repo)
    report["checks"]["mini_worktree"] = {
        **status,
        "status": "PASS" if status["returncode"] == 0 and not status["stdout"].strip() else "FAIL",
    }

    report["checks"]["benchmark_config"] = _check_config(mini_repo)

    docker_version = _run(["docker", "--version"])
    report["checks"]["docker_cli"] = {
        **docker_version,
        "status": "PASS" if docker_version["returncode"] == 0 else "FAIL",
    }

    docker_info = _run(["docker", "info", "--format", "{{json .ServerVersion}}"])
    report["checks"]["docker_daemon"] = {
        **docker_info,
        "status": "PASS" if docker_info["returncode"] == 0 else "FAIL",
    }

    if args.probe_image:
        probe = _run(
            ["docker", "run", "--rm", args.probe_image, "/bin/sh", "-lc",
             "echo codepro-benchmark-substrate-ok"],
            timeout=120,
        )
        report["checks"]["container_probe"] = {
            **probe,
            "image": args.probe_image,
            "status": (
                "PASS"
                if probe["returncode"] == 0
                and "codepro-benchmark-substrate-ok" in probe["stdout"]
                else "FAIL"
            ),
        }
    else:
        report["checks"]["container_probe"] = {
            "status": "NOT_EXECUTED",
            "reason": "NO_PROBE_IMAGE_SUPPLIED",
        }

    required = ("mini_commit", "mini_worktree", "benchmark_config", "docker_cli", "docker_daemon")
    if all(report["checks"][name]["status"] == "PASS" for name in required):
        probe_status = report["checks"]["container_probe"]["status"]
        report["classification"] = (
            "BENCHMARK_SUBSTRATE_READY"
            if probe_status in {"PASS", "NOT_EXECUTED"}
            else "BLOCKED"
        )

    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    sys.stdout.write(rendered)
    return 0 if report["classification"] == "BENCHMARK_SUBSTRATE_READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
