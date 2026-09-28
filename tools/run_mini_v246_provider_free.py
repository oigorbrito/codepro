#!/usr/bin/env python3
"""Run the complete mini-SWE-agent v2.4.6 provider-free qualification locally.

This is an orchestration wrapper around the already-frozen CodePro reference
integration. It does not call any model/provider and does not claim benchmark
resolution. It exists to make the provider-free qualification reproducible as
one command on a machine with Git, Python and Docker.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import venv
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MINI_REPO_URL = "https://github.com/SWE-agent/mini-swe-agent.git"
MINI_VERSION = "v2.4.6"
MINI_SHA = "a83fcae82d2a08f0ee0c688f9d137b3566c097f8"
MINI_CONFIG = "src/minisweagent/config/benchmarks/swebench.yaml"
MINI_CONFIG_BLOB = "106decd160e72e5164e29d15d23da354c29c309d"
DEFAULT_INSTANCE = "sympy__sympy-14711"


def run(
    argv: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 1800,
    check: bool = False,
) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    try:
        p = subprocess.run(
            argv,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            check=False,
        )
        result = {
            "argv": argv,
            "cwd": str(cwd) if cwd else None,
            "started_at": started,
            "returncode": p.returncode,
            "stdout": p.stdout,
            "stderr": p.stderr,
            "timeout": False,
            "error": None,
        }
    except subprocess.TimeoutExpired as exc:
        result = {
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
        result = {
            "argv": argv,
            "cwd": str(cwd) if cwd else None,
            "started_at": started,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "timeout": False,
            "error": f"{type(exc).__name__}: {exc}",
        }

    if check and result["returncode"] != 0:
        raise RuntimeError(json.dumps(result, ensure_ascii=False))
    return result


def venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def record(report: dict[str, Any], name: str, result: dict[str, Any]) -> bool:
    report["steps"][name] = result
    return result.get("returncode") == 0 and not result.get("timeout")


def write_report(output_dir: Path, report: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "runner-summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "logs" / "architecture" / "mini-v246-provider-free-local",
    )
    parser.add_argument("--instance", default=DEFAULT_INSTANCE)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--probe-image", default="python:3.11-slim")
    args = parser.parse_args()

    if args.repeat < 1:
        parser.error("--repeat must be >= 1")

    output_dir = args.output_dir.expanduser().resolve()
    report: dict[str, Any] = {
        "schema_version": 1,
        "classification": "BLOCKED_NOT_EXECUTED",
        "provider_called": False,
        "codepro_root": str(ROOT),
        "reference": {
            "repository": MINI_REPO_URL,
            "version": MINI_VERSION,
            "commit": MINI_SHA,
            "config_path": MINI_CONFIG,
            "config_blob": MINI_CONFIG_BLOB,
        },
        "inputs": {
            "instance": args.instance,
            "repeat": args.repeat,
            "probe_image": args.probe_image,
        },
        "steps": {},
    }
    write_report(output_dir, report)

    # Gate 0: local tools.
    for tool in ("git", "docker"):
        path = shutil.which(tool)
        report["steps"][f"tool_{tool}"] = {"path": path, "status": "PASS" if path else "FAIL"}
        if not path:
            report["classification"] = f"BLOCKED_{tool.upper()}_UNAVAILABLE"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

    docker_version = run(["docker", "--version"], timeout=30)
    if not record(report, "docker_version", docker_version):
        report["classification"] = "BLOCKED_DOCKER_CLI"
        write_report(output_dir, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    docker_info = run(["docker", "info"], timeout=60)
    if not record(report, "docker_daemon", docker_info):
        report["classification"] = "BLOCKED_DOCKER_DAEMON"
        write_report(output_dir, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    focused = run(
        [
            sys.executable,
            "-m",
            "unittest",
            "-v",
            "tests.test_minisweagent_benchmark_reference",
            "tests.test_minisweagent_preflight",
            "tests.test_minisweagent_provider_free_task_harness",
        ],
        cwd=ROOT,
        timeout=300,
    )
    if not record(report, "focused_contract_tests", focused):
        report["classification"] = "BLOCKED_LOCAL_CONTRACT_TESTS"
        write_report(output_dir, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    with tempfile.TemporaryDirectory(prefix="codepro-mini-v246-") as tmp:
        temp = Path(tmp)
        mini_repo = temp / "mini-swe-agent"
        env_dir = temp / "venv"

        clone = run(["git", "clone", "--filter=blob:none", "--no-checkout", MINI_REPO_URL, str(mini_repo)], timeout=600)
        if not record(report, "clone_upstream", clone):
            report["classification"] = "BLOCKED_UPSTREAM_FETCH"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

        fetch = run(["git", "fetch", "--depth", "1", "origin", MINI_SHA], cwd=mini_repo, timeout=600)
        if not record(report, "fetch_exact_commit", fetch):
            # Fallback is only another way to obtain the same immutable tag/commit,
            # never a different reference.
            fetch = run(["git", "fetch", "--depth", "1", "origin", f"refs/tags/{MINI_VERSION}:refs/tags/{MINI_VERSION}"], cwd=mini_repo, timeout=600)
            if not record(report, "fetch_exact_tag_fallback", fetch):
                report["classification"] = "BLOCKED_UPSTREAM_FETCH"
                write_report(output_dir, report)
                print(json.dumps(report, ensure_ascii=False, indent=2))
                return 2

        checkout = run(["git", "checkout", "--detach", MINI_SHA], cwd=mini_repo, timeout=120)
        if not record(report, "checkout_exact_commit", checkout):
            report["classification"] = "BLOCKED_REFERENCE_IDENTITY"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

        head = run(["git", "rev-parse", "HEAD"], cwd=mini_repo, timeout=30)
        blob = run(["git", "rev-parse", f"HEAD:{MINI_CONFIG}"], cwd=mini_repo, timeout=30)
        clean = run(["git", "status", "--porcelain"], cwd=mini_repo, timeout=30)
        record(report, "mini_head", head)
        record(report, "mini_config_blob", blob)
        record(report, "mini_worktree", clean)

        identity_ok = (
            head.get("stdout", "").strip() == MINI_SHA
            and blob.get("stdout", "").strip() == MINI_CONFIG_BLOB
            and not clean.get("stdout", "").strip()
        )
        if not identity_ok:
            report["classification"] = "BLOCKED_REFERENCE_IDENTITY"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

        venv.EnvBuilder(with_pip=True, clear=True).create(env_dir)
        py = venv_python(env_dir)

        install = run(
            [
                str(py),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-input",
                str(mini_repo),
            ],
            timeout=1200,
        )
        if not record(report, "install_pinned_mini", install):
            report["classification"] = "BLOCKED_MINI_INSTALL"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

        pip_check = run([str(py), "-m", "pip", "check"], timeout=120)
        if not record(report, "pip_check", pip_check):
            report["classification"] = "BLOCKED_MINI_INSTALL"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

        preflight_path = ROOT / "experiments" / "integrations" / "minisweagent" / "preflight.py"
        preflight_json = output_dir / "preflight.json"
        preflight = run(
            [
                str(py),
                str(preflight_path),
                "--mini-repo",
                str(mini_repo),
                "--probe-image",
                args.probe_image,
                "--output",
                str(preflight_json),
            ],
            cwd=ROOT,
            timeout=900,
        )
        if not record(report, "provider_free_preflight", preflight):
            report["classification"] = "BLOCKED_PROVIDER_FREE_PREFLIGHT"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

        harness_path = ROOT / "experiments" / "integrations" / "minisweagent" / "provider_free_task_harness.py"
        task_json = output_dir / "task-environment.json"
        task_probe = run(
            [
                str(py),
                str(harness_path),
                "--mini-repo",
                str(mini_repo),
                "--subset",
                "verified",
                "--split",
                "test",
                "--instance",
                args.instance,
                "--repeat",
                str(args.repeat),
                "--output",
                str(task_json),
            ],
            cwd=ROOT,
            timeout=3600,
        )
        if not record(report, "provider_free_task_environment", task_probe):
            report["classification"] = "BLOCKED_PROVIDER_FREE_TASK_ENVIRONMENT"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

    report["classification"] = "REFERENCE_PROVIDER_FREE_TASK_ENV_READY"
    write_report(output_dir, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
