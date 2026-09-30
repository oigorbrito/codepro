#!/usr/bin/env python3
"""Run the controlled Phase 7R S4-R3 context requalification cell."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).parents[1].resolve()
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import run_phase7_s4_openhands as s4  # noqa: E402

BASE_EVIDENCE = ROOT / "evidence" / "phase7r-s4-runtime-requalification" / "S4-OpenHands-parallel1-litellm1943-ctx16384"


def next_evidence_dir() -> Path:
    if not BASE_EVIDENCE.exists() or not any(BASE_EVIDENCE.iterdir()):
        return BASE_EVIDENCE
    attempt = 2
    while True:
        candidate = BASE_EVIDENCE.with_name(f"{BASE_EVIDENCE.name}-attempt-{attempt}")
        if not candidate.exists() or not any(candidate.iterdir()):
            return candidate
        attempt += 1


if __name__ == "__main__":
    evidence = next_evidence_dir()
    print(f"S4_R3_EVIDENCE_DIR = {evidence}")
    raise SystemExit(
        s4.main(
            [
                "--evidence-dir",
                str(evidence),
                "--study-id",
                "phase7r-s4-r3-context16384",
                "--llama-parallel",
                "1",
                "--llama-context",
                "16384",
                "--litellm-version",
                "1.94.3",
            ]
        )
    )
