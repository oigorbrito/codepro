#!/usr/bin/env python3
"""Independent evidence-only review of the exact CodePro release candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


EXPECTED_CANDIDATE_SHA = "eb350cc5c9c7c2430e86a3870a6a40f67038d363"


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(label: str, failures: list[str]) -> None:
    failures.append(label)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--m1-evidence-root", required=True, type=Path)
    parser.add_argument("--m2-m3-evidence-root", required=True, type=Path)
    parser.add_argument("--m4-m5-evidence-root", required=True, type=Path)
    args = parser.parse_args()

    m1 = args.m1_evidence_root.expanduser().resolve()
    m23 = args.m2_m3_evidence_root.expanduser().resolve()
    m45 = args.m4_m5_evidence_root.expanduser().resolve()

    acceptance_path = m1 / "acceptance.json"
    m23_path = m23 / "m2-m3-summary.json"
    m45_path = m45 / "m4-m5-readiness-summary.json"
    output = m45 / "release-candidate-acceptance.json"

    report: dict[str, Any] = {
        "schema_version": 1,
        "classification": "BLOCKED_RELEASE_CANDIDATE_REVIEW",
        "candidate_sha": EXPECTED_CANDIDATE_SHA,
        "authority_ref": "acceptance://independent-release-candidate-review",
        "independent_of_executor": True,
        "release": "NOT_AUTHORIZED",
        "publication": "NOT_AUTHORIZED",
        "activation": "NOT_AUTHORIZED",
        "executor_promotion": "NOT_AUTHORIZED",
        "evidence_refs": [],
        "failures": [],
    }

    failures: list[str] = report["failures"]
    for path in (acceptance_path, m23_path, m45_path):
        if not path.is_file():
            fail(f"missing evidence: {path.name}", failures)
    if failures:
        return finish(report, output, 2)

    try:
        m1p = load_object(acceptance_path)
        m23p = load_object(m23_path)
        m45p = load_object(m45_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        fail(f"invalid evidence: {type(exc).__name__}: {exc}", failures)
        return finish(report, output, 2)

    report["evidence_refs"] = [
        {"path": str(acceptance_path), "sha256": sha256(acceptance_path)},
        {"path": str(m23_path), "sha256": sha256(m23_path)},
        {"path": str(m45_path), "sha256": sha256(m45_path)},
    ]

    if (m1p.get("decision") or {}).get("status") != "ACCEPTED":
        fail("M1 acceptance is not ACCEPTED", failures)
    if m1p.get("promotion") != "NOT_AUTHORIZED":
        fail("M1 acceptance unexpectedly authorizes promotion", failures)

    if m23p.get("classification") != "M2_M3_VALIDATED":
        fail("M2/M3 classification mismatch", failures)
    expected_m2 = {
        "failure": "FAILED",
        "timeout": "TIMED_OUT",
        "environment_unavailable": "ENVIRONMENT_UNAVAILABLE",
    }
    for name, status in expected_m2.items():
        if ((m23p.get("m2") or {}).get(name) or {}).get("status") != status:
            fail(f"M2 state mismatch: {name}", failures)
    comparison = (m23p.get("m3") or {}).get("comparison") or {}
    for key in (
        "both_verified",
        "distinct_attempt_id",
        "distinct_run_id",
        "same_base_sha",
        "same_changed_files",
        "same_patch_sha256",
        "same_task_id",
    ):
        if comparison.get(key) is not True:
            fail(f"M3 comparison failed: {key}", failures)
    if m23p.get("provider_called") is not False or m23p.get("model_called") is not False:
        fail("M2/M3 provider/model invariant failed", failures)

    if m45p.get("classification") != "M4_M5_READINESS_VALIDATED":
        fail("M4/M5 readiness classification mismatch", failures)
    if m45p.get("candidate_sha") != EXPECTED_CANDIDATE_SHA:
        fail("candidate SHA mismatch", failures)
    if (m45p.get("m4") or {}).get("classification") != "M4_PRIVATE_INSTALL_AND_USE_VALIDATED":
        fail("M4 classification mismatch", failures)
    if (m45p.get("m5") or {}).get("classification") != "M5_RELEASE_CANDIDATE_READY_FOR_INDEPENDENT_REVIEW":
        fail("M5 classification mismatch", failures)

    prior = (m45p.get("m5") or {}).get("prior_evidence") or {}
    if prior.get("m1_status") != "ACCEPTED":
        fail("M5 prior M1 evidence mismatch", failures)
    if prior.get("m2_m3_classification") != "M2_M3_VALIDATED":
        fail("M5 prior M2/M3 evidence mismatch", failures)
    if prior.get("m1_acceptance_sha256") != sha256(acceptance_path):
        fail("M1 evidence hash mismatch", failures)
    if prior.get("m2_m3_summary_sha256") != sha256(m23_path):
        fail("M2/M3 evidence hash mismatch", failures)

    installed = (m45p.get("m4") or {}).get("installed_vertical_result") or {}
    if installed.get("status") != "VERIFIED":
        fail("installed vertical not VERIFIED", failures)

    checks = (m45p.get("m5") or {}).get("candidate_checks") or {}
    for name in ("foundation", "baseline", "full_suite", "mutation_probe", "fingerprint", "compileall"):
        if (checks.get(name) or {}).get("returncode") != 0:
            fail(f"candidate check failed: {name}", failures)

    identity = (m45p.get("m5") or {}).get("candidate_identity") or {}
    if ((identity.get("head") or {}).get("stdout") or "").strip() != EXPECTED_CANDIDATE_SHA:
        fail("candidate identity head mismatch", failures)
    if ((identity.get("status") or {}).get("stdout") or "").strip():
        fail("candidate checkout not clean", failures)

    for key in ("provider_called", "model_called"):
        if m45p.get(key) is not False:
            fail(f"M4/M5 {key} invariant failed", failures)
    for key in ("release", "publication", "activation", "executor_promotion"):
        if m45p.get(key) != "NOT_AUTHORIZED":
            fail(f"M4/M5 unexpectedly authorized {key}", failures)

    if failures:
        return finish(report, output, 2)

    report["classification"] = "RELEASE_CANDIDATE_ACCEPTED_FOR_RELEASE_DECISION"
    report["rationale"] = (
        "Independent evidence-only review confirmed the exact candidate SHA, "
        "M1 acceptance, M2 negative-state separation, M3 reproducibility, "
        "M4 private install/use, and all M5 candidate checks. This authorizes "
        "a release decision review only; it does not create or publish a release."
    )
    return finish(report, output, 0)


def finish(report: dict[str, Any], path: Path, code: int) -> int:
    if path.exists():
        raise FileExistsError(f"review evidence already exists: {path}")
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(rendered, encoding="utf-8", newline="\n")
    sys.stdout.write(rendered)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
