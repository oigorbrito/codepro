#!/usr/bin/env python3
"""Run the controlled Phase 7R Phase 7Q S4-L1-Q1 scaffold/model pair cell."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).parents[1].resolve()
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import run_phase7_s4_openhands as s4  # noqa: E402

BASE_EVIDENCE = ROOT / "evidence" / "phase7r-s4-runtime-requalification" / "S4-L1-Nanbeige42-parallel1-litellm1943-ctx16384-timeout600-winps2-inlineprompt2-maxiter10-single-workspace"


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
    print(f"S4_L1_Q1_EVIDENCE_DIR = {evidence}")
    raise SystemExit(
        s4.main(
            [
                "--evidence-dir",
                str(evidence),
                "--study-id",
                "phase7q-s4-l1-q1-nanbeige42-pair",
                "--llama-parallel",
                "1",
                "--llama-context",
                "16384",
                "--litellm-version",
                "1.94.3",
                "--conversation-timeout-seconds",
                "600",
                "--executor-timeout-seconds",
                "660",
                "--vertical-wall-time-seconds",
                "720",
                "--platform-contract",
                "windows-powershell-v2",
                "--system-prompt-profile",
                "windows-embedded-v1",
                "--conversation-worktree",
                "false",
                "--cleanup-untracked-python-bytecode",
                "true",
                "--max-iterations",
                "10",
                "--model-path",
                r"D:\\projetos\\codepro-mini-runtime\\models\\phase4\\L1-Nanbeige4.2-3B\\Nanbeige4.2-3B-Q4_K_M-mainline-e31e82d.gguf",
                "--model-bytes",
                "2574807872",
                "--model-sha256",
                "FBCE43B8977DD73A86126E85AE0BFE219EF3131498AE7C37571DEA58F3C6AA34",
                "--model-alias",
                "codepro-phase7q-nanbeige42-3b",
            ]
        )
    )
