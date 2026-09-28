#!/usr/bin/env python3
"""Verify published CodePro prerelease identity and hand off to maintenance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from typing import Any


REPO = "oigorbrito/codepro"
TAG = "v0.3.0.dev0"
EXPECTED_COMMIT = "eb350cc5c9c7c2430e86a3870a6a40f67038d363"
EXPECTED_VERSION = "0.3.0.dev0"


def run(argv: list[str], *, cwd: Path) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            argv,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            check=False,
            timeout=120,
        )
        return {
            "argv": argv,
            "cwd": str(cwd),
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "error": None,
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "argv": argv,
            "cwd": str(cwd),
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--evidence-dir", required=True, type=Path)
    args = parser.parse_args()

    root = args.repo_root.expanduser().resolve()
    evidence = args.evidence_dir.expanduser().resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    output = evidence / "post-release-integrity.json"
    if output.exists():
        raise FileExistsError(output)

    report: dict[str, Any] = {
        "schema_version": 1,
        "classification": "BLOCKED_POST_RELEASE_INTEGRITY",
        "tag": TAG,
        "expected_commit": EXPECTED_COMMIT,
        "expected_version": EXPECTED_VERSION,
        "package_index_publication": "NOT_AUTHORIZED",
        "activation": "NOT_AUTHORIZED",
        "executor_promotion": "NOT_AUTHORIZED",
        "maintenance": "NOT_STARTED",
        "steps": {},
        "failures": [],
    }

    fetch = run(["git", "fetch", "origin", "--tags"], cwd=root)
    peel = run(["git", "rev-parse", f"{TAG}^{{}}"], cwd=root)
    show_version = run(
        ["git", "show", f"{TAG}:src/arkx/__init__.py"],
        cwd=root,
    )
    release = run(
        [
            "gh",
            "release",
            "view",
            TAG,
            "--repo",
            REPO,
            "--json",
            "tagName,name,isPrerelease,isDraft,url",
        ],
        cwd=root,
    )
    report["steps"] = {
        "fetch_tags": fetch,
        "tag_peel": peel,
        "candidate_version_file": show_version,
        "release_view": release,
    }

    failures = report["failures"]
    if fetch["returncode"] != 0:
        failures.append("fetch tags failed")
    if peel["returncode"] != 0 or peel["stdout"].strip() != EXPECTED_COMMIT:
        failures.append("tag does not dereference to accepted candidate")
    if (
        show_version["returncode"] != 0
        or f'__version__ = "{EXPECTED_VERSION}"' not in show_version["stdout"]
    ):
        failures.append("candidate package version mismatch")

    try:
        release_payload = json.loads(release["stdout"]) if release["returncode"] == 0 else {}
    except json.JSONDecodeError:
        release_payload = {}
    report["release"] = release_payload
    if release_payload.get("tagName") != TAG:
        failures.append("release tag mismatch")
    if release_payload.get("isPrerelease") is not True:
        failures.append("release is not prerelease")
    if release_payload.get("isDraft") is not False:
        failures.append("release draft state mismatch")

    if failures:
        return finish(report, output, 2)

    report["classification"] = "POST_RELEASE_INTEGRITY_VALIDATED"
    report["maintenance"] = "BASELINE_ESTABLISHED"
    return finish(report, output, 0)


def finish(report: dict[str, Any], output: Path, code: int) -> int:
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    output.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
