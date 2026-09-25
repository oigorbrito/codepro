#!/usr/bin/env python3
"""Validate complete workspace patch evidence after v0.3.0.dev0."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).parents[1].resolve()
SRC = ROOT / "src"


def run(argv: list[str], *, timeout: int = 600) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC)
    try:
        completed = subprocess.run(
            argv,
            cwd=str(ROOT),
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


def main() -> int:
    report: dict[str, Any] = {
        "schema_version": 1,
        "classification": "BLOCKED_PATCH_EVIDENCE_HARDENING",
        "release_baseline": "v0.3.0.dev0",
        "release": "UNCHANGED",
        "provider_called": False,
        "model_called": False,
        "package_index_publication": "NOT_AUTHORIZED",
        "activation": "NOT_AUTHORIZED",
        "executor_promotion": "NOT_AUTHORIZED",
    }

    focused = run([sys.executable, "-m", "unittest", "-v", "tests.test_vertical"])
    report["focused_tests"] = focused
    if focused["returncode"] != 0:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    full = run([
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-t",
        ".",
        "-v",
    ])
    report["full_suite"] = full
    if full["returncode"] != 0:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    report["classification"] = "PATCH_EVIDENCE_HARDENING_VALIDATED"
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
