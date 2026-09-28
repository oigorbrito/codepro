#!/usr/bin/env python3
"""Integrated next-release readiness gate.

This gate decides only whether the current post-release maintenance HEAD has
enough local evidence for a separate release decision. It does not publish,
tag, sign, activate, promote, or claim CI success.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).parents[1].resolve()
SRC = ROOT / "src"
TOOLS = ROOT / "tools"
PUBLISHED_BASELINE = "eb350cc5c9c7c2430e86a3870a6a40f67038d363"
PUBLISHED_TAG = "v0.3.0.dev0"
CURRENT_VERSION = "0.3.0.dev0"


def run(
    argv: list[str],
    *,
    timeout: int = 1800,
    pythonpath: bool = False,
) -> dict[str, Any]:
    env = os.environ.copy()
    if pythonpath:
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
    except OSError as exc:
        return {
            "argv": argv,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "timeout": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def parse_gate(observation: dict[str, Any]) -> dict[str, Any]:
    if observation["returncode"] != 0:
        return {
            "returncode": observation["returncode"],
            "timeout": observation["timeout"],
            "error": observation["error"],
            "classification": None,
            "parse_error": None,
        }
    try:
        payload = json.loads(observation["stdout"])
    except json.JSONDecodeError as exc:
        return {
            "returncode": observation["returncode"],
            "timeout": observation["timeout"],
            "error": observation["error"],
            "classification": None,
            "parse_error": str(exc),
        }
    return {
        "returncode": observation["returncode"],
        "timeout": observation["timeout"],
        "error": observation["error"],
        "classification": payload.get("classification"),
        "source_revision": (
            payload.get("source_revision")
            or payload.get("head", {}).get("stdout", "").strip()
        ),
        "release": payload.get("release"),
        "package_index_publication": payload.get("package_index_publication"),
        "release_asset_upload": payload.get("release_asset_upload"),
        "activation": payload.get("activation"),
        "executor_promotion": payload.get("executor_promotion"),
        "cryptographic_signing": payload.get("cryptographic_signing"),
        "hosted_attestation": payload.get("hosted_attestation"),
        "reproducibility": payload.get("reproducibility"),
        "offline_verification": payload.get("offline_verification"),
        "clean_install": payload.get("clean_install"),
        "artifacts": payload.get("artifacts"),
        "sbom": payload.get("sbom"),
        "provenance": payload.get("provenance"),
        "full_suite_returncode": (
            payload.get("full_suite", {}).get("returncode")
            if isinstance(payload.get("full_suite"), dict)
            else None
        ),
        "parse_error": None,
    }


def main() -> int:
    report: dict[str, Any] = {
        "schema_version": 1,
        "classification": "BLOCKED_RELEASE_READINESS",
        "published_release_baseline": PUBLISHED_TAG,
        "published_release_commit": PUBLISHED_BASELINE,
        "release": "UNCHANGED",
        "new_release": "NOT_AUTHORIZED",
        "stable_v0_3_0": "NOT_AUTHORIZED",
        "package_index_publication": "NOT_AUTHORIZED",
        "release_asset_upload": "NOT_AUTHORIZED",
        "production_activation": "NOT_AUTHORIZED",
        "executor_promotion": "NOT_AUTHORIZED",
        "ci_status": "NOT_EXECUTED_OR_NOT_VERIFIED",
        "cryptographic_signing": "NOT_PERFORMED",
        "hosted_attestation": "NOT_PERFORMED",
        "provider_called": False,
        "model_called": False,
        "steps": {},
        "failures": [],
    }

    head = run(["git", "rev-parse", "HEAD"])
    tracked = run(["git", "status", "--porcelain=v1", "--untracked-files=no"])
    untracked_before = run(["git", "ls-files", "--others", "--exclude-standard"])
    baseline = run(["git", "rev-parse", PUBLISHED_BASELINE])
    tag_target = run(["git", "rev-parse", f"{PUBLISHED_TAG}^{{}}"])
    ancestry = run(["git", "merge-base", "--is-ancestor", PUBLISHED_BASELINE, "HEAD"])
    commit_count = run(["git", "rev-list", "--count", f"{PUBLISHED_BASELINE}..HEAD"])
    change_summary = run(
        ["git", "diff", "--stat", "--compact-summary", f"{PUBLISHED_BASELINE}..HEAD"]
    )
    commit_log = run(
        ["git", "log", "--format=%H%x09%s", "--reverse", f"{PUBLISHED_BASELINE}..HEAD"]
    )

    report["steps"]["head"] = head
    report["steps"]["tracked_status_before"] = tracked
    report["steps"]["untracked_before"] = untracked_before
    report["steps"]["published_baseline"] = baseline
    report["steps"]["published_tag_target"] = tag_target
    report["steps"]["baseline_is_ancestor"] = ancestry
    report["steps"]["commit_count_since_baseline"] = commit_count
    report["steps"]["change_summary"] = change_summary

    if head["returncode"] != 0:
        report["failures"].append("HEAD_UNAVAILABLE")
    if tracked["returncode"] != 0 or tracked["stdout"].strip():
        report["failures"].append("TRACKED_WORKTREE_NOT_CLEAN")
    if untracked_before["returncode"] != 0:
        report["failures"].append("UNTRACKED_STATE_UNAVAILABLE")
    if baseline["returncode"] != 0 or baseline["stdout"].strip() != PUBLISHED_BASELINE:
        report["failures"].append("PUBLISHED_BASELINE_UNAVAILABLE")
    if tag_target["returncode"] != 0 or tag_target["stdout"].strip() != PUBLISHED_BASELINE:
        report["failures"].append("PUBLISHED_TAG_TARGET_MISMATCH")
    if ancestry["returncode"] != 0:
        report["failures"].append("PUBLISHED_BASELINE_NOT_ANCESTOR")

    if report["failures"]:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    candidate_head = head["stdout"].strip()
    report["candidate_head"] = candidate_head
    report["commit_count_since_published_baseline"] = int(commit_count["stdout"].strip())
    report["changes_since_published_baseline"] = [
        line.split("\t", 1)
        for line in commit_log["stdout"].splitlines()
        if line.strip() and "\t" in line
    ]
    report["change_summary"] = change_summary["stdout"].strip()

    version = run(
        [
            sys.executable,
            "-c",
            "import arkx; print(arkx.__version__)",
        ],
        pythonpath=True,
    )
    report["steps"]["package_version"] = version
    if version["returncode"] != 0 or version["stdout"].strip() != CURRENT_VERSION:
        report["failures"].append("PACKAGE_VERSION_IDENTITY_MISMATCH")

    runtime_observation = run(
        [sys.executable, str(TOOLS / "run_runtime_evidence_hardening_validation.py")],
        timeout=1800,
    )
    runtime_gate = parse_gate(runtime_observation)
    report["runtime_evidence_gate"] = runtime_gate
    if (
        runtime_gate["returncode"] != 0
        or runtime_gate["classification"] != "RUNTIME_EVIDENCE_HARDENING_VALIDATED"
    ):
        report["failures"].append("RUNTIME_EVIDENCE_GATE_FAILED")

    supply_observation = run(
        [sys.executable, str(TOOLS / "run_local_supply_chain_validation.py")],
        timeout=1800,
    )
    supply_gate = parse_gate(supply_observation)
    report["local_supply_chain_gate"] = supply_gate
    if (
        supply_gate["returncode"] != 0
        or supply_gate["classification"] != "LOCAL_SUPPLY_CHAIN_BASELINE_VALIDATED"
    ):
        report["failures"].append("LOCAL_SUPPLY_CHAIN_GATE_FAILED")

    if runtime_gate.get("source_revision") not in (None, "", candidate_head):
        report["failures"].append("RUNTIME_GATE_REVISION_MISMATCH")
    if supply_gate.get("source_revision") != candidate_head:
        report["failures"].append("SUPPLY_CHAIN_GATE_REVISION_MISMATCH")

    tracked_after = run(["git", "status", "--porcelain=v1", "--untracked-files=no"])
    untracked_after = run(["git", "ls-files", "--others", "--exclude-standard"])
    report["steps"]["tracked_status_after"] = tracked_after
    report["steps"]["untracked_after"] = untracked_after

    if tracked_after["returncode"] != 0 or tracked_after["stdout"].strip():
        report["failures"].append("TRACKED_WORKTREE_MUTATED")
    if (
        untracked_after["returncode"] != 0
        or untracked_after["stdout"] != untracked_before["stdout"]
    ):
        report["failures"].append("UNTRACKED_WORKTREE_MUTATED")

    report["known_limitations"] = [
        "GitHub Actions/official CI PASS is not established by this local gate.",
        "The published v0.3.0.dev0 tag is unsigned.",
        "Current local provenance is unsigned and no hosted attestation is claimed.",
        "The package version remains 0.3.0.dev0; a future release identifier/version requires a separate release decision.",
        "No release asset upload, package-index publication, production activation, or executor promotion is authorized.",
    ]

    report["decision_scope"] = (
        "Ready for a separate human release decision only; this gate does not authorize or perform a release."
    )

    if report["failures"]:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    report["classification"] = "READY_FOR_RELEASE_DECISION"
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
