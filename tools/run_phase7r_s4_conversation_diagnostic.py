#!/usr/bin/env python3
"""Repeat S4-R1 unchanged to capture Agent Server conversation-state diagnostics."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).parents[1].resolve()
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import run_phase7_s4_openhands as s4  # noqa: E402

EVIDENCE = ROOT / "evidence" / "phase7r-s4-runtime-requalification" / "S4-OpenHands-parallel1-diagnostic"

if __name__ == "__main__":
    raise SystemExit(
        s4.main(
            [
                "--evidence-dir",
                str(EVIDENCE),
                "--study-id",
                "phase7r-s4-conversation-state-diagnostic",
                "--llama-parallel",
                "1",
            ]
        )
    )
