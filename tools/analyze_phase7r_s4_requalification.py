#!/usr/bin/env python3
"""Analyze Phase 7R S4-R1 local evidence without changing the experiment."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1].resolve()
EVIDENCE = ROOT / "evidence" / "phase7r-s4-runtime-requalification" / "S4-OpenHands-parallel1"

FILES = {
    "summary": EVIDENCE / "s4-summary.json",
    "adapter": EVIDENCE / "openhands-result.json",
    "canvas_stdout": EVIDENCE / "agent-canvas-stdout.txt",
    "canvas_stderr": EVIDENCE / "agent-canvas-stderr.txt",
    "llama_stdout": EVIDENCE / "llama-server-stdout.txt",
    "llama_stderr": EVIDENCE / "llama-server-stderr.txt",
}

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""

def main() -> int:
    missing = [name for name, path in FILES.items() if not path.is_file()]
    if missing:
        raise SystemExit(f"missing evidence files: {', '.join(missing)}")

    summary = json.loads(read_text(FILES["summary"]))
    adapter = json.loads(read_text(FILES["adapter"]))
    canvas = read_text(FILES["canvas_stdout"]) + "\n" + read_text(FILES["canvas_stderr"])
    llama = read_text(FILES["llama_stdout"]) + "\n" + read_text(FILES["llama_stderr"])

    context_signals = [
        "Context size has been exceeded",
        "failed to find free space in the KV cache",
        "failed to find a memory slot",
        "decode() failed",
    ]
    agent_signals = [
        "litellm.InternalServerError",
        "Conversation lease lost",
        "Exited with code 1",
    ]

    report = {
        "study_id": summary.get("study_id"),
        "classification": summary.get("classification"),
        "conversation_id": adapter.get("conversation_id"),
        "parallel": (summary.get("local_runtime") or {}).get("parallel"),
        "context_or_kv_pressure_observed": any(s.lower() in llama.lower() or s.lower() in canvas.lower() for s in context_signals),
        "context_or_kv_matches": {s: (llama.lower().count(s.lower()) + canvas.lower().count(s.lower())) for s in context_signals},
        "agent_failure_matches": {s: canvas.lower().count(s.lower()) for s in agent_signals},
        "edit_observed": (summary.get("gates") or {}).get("edit_observed"),
        "patch_captured": (summary.get("gates") or {}).get("patch_captured"),
        "independent_verifier": (summary.get("gates") or {}).get("independent_verifier"),
        "model_calls_observed": (summary.get("gates") or {}).get("model_calls_observed"),
    }

    if report["context_or_kv_pressure_observed"]:
        report["attribution"] = "RUNTIME_CONTEXT_OR_KV_PRESSURE_PERSISTS_WITH_PARALLEL_1"
        report["next_gate"] = "EXPLICIT_CONTEXT_TREATMENT_DECISION_REQUIRED"
    else:
        report["attribution"] = "NO_CONTEXT_OR_KV_PRESSURE_OBSERVED_IN_R1_LOGS"
        report["next_gate"] = "AGENT_SERVER_CONVERSATION_STATE_DIAGNOSTIC_REQUIRED"

    out = EVIDENCE / "phase7r-analysis.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
