#!/usr/bin/env python3
"""Run and close the Phase 7 S2 Agentless compatibility block."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).parents[1].resolve()
BRANCH = "phase7/scaffold-compatibility"
EVIDENCE = ROOT / "evidence" / "phase7-scaffold-compatibility" / "S2-Agentless"
DIAGNOSTICS = ROOT / "evidence" / "phase7-scaffold-compatibility" / "diagnostics"
MANIFEST = ROOT / "experiments" / "phase7" / "scaffold-pool.json"
AUDIT = ROOT / "docs" / "audits" / "phase7-s2-agentless-20260928.md"

def run(argv: list[str], *, env: dict[str, str] | None = None, check: bool = True, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", shell=False, check=False, timeout=timeout)
    if completed.stdout:
        sys.stdout.write(completed.stdout)
    if completed.stderr:
        sys.stderr.write(completed.stderr)
    if check and completed.returncode != 0:
        raise RuntimeError(f"command failed ({completed.returncode}): {argv!r}")
    return completed

def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], check=check)

def archive_prior() -> None:
    if not EVIDENCE.exists():
        return
    summary_path = EVIDENCE / "s2-summary.json"
    classification = "INCOMPLETE"
    if summary_path.is_file():
        try:
            classification = str(json.loads(summary_path.read_text(encoding="utf-8")).get("classification") or "UNKNOWN")
        except (OSError, json.JSONDecodeError):
            classification = "UNREADABLE"
    DIAGNOSTICS.mkdir(parents=True, exist_ok=True)
    attempt = len([item for item in DIAGNOSTICS.iterdir() if item.is_dir() and item.name.startswith("s2-attempt-")]) + 1
    label = re.sub(r"[^a-z0-9]+", "-", classification.lower()).strip("-") or "unknown"
    while True:
        archive = DIAGNOSTICS / f"s2-attempt-{attempt}-{label}"
        if not archive.exists():
            break
        attempt += 1
    shutil.move(str(EVIDENCE), str(archive))
    print(f"PREVIOUS_S2_ATTEMPT_ARCHIVED = {archive}")

def update_manifest(summary: dict) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    found = False
    for candidate in manifest.get("candidates", []):
        if candidate.get("id") != "S2":
            continue
        found = True
        candidate["phase7_status"] = summary["classification"]
        candidate["evidence"] = "evidence/phase7-scaffold-compatibility/S2-Agentless/s2-summary.json"
        candidate["observed"] = {
            "vertical_status": (summary.get("vertical") or {}).get("status"),
            "vertical_reason": (summary.get("vertical") or {}).get("reason"),
            "model_calls": (summary.get("telemetry") or {}).get("model_calls"),
            "prompt_tokens": (summary.get("telemetry") or {}).get("prompt_tokens"),
            "completion_tokens": (summary.get("telemetry") or {}).get("completion_tokens"),
            "native_contract": summary.get("native_contract"),
            "native_command_loop": summary.get("native_command_loop"),
            "gates": summary.get("gates"),
            "blocker": summary.get("blocker"),
        }
        break
    if not found:
        raise RuntimeError("S2 candidate missing from manifest")
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

def write_audit(summary: dict) -> None:
    gates = summary.get("gates") or {}
    telemetry = summary.get("telemetry") or {}
    vertical = summary.get("vertical") or {}
    adapter = summary.get("adapter") or {}
    lines = [
        "# Phase 7 S2 - Agentless compatibility audit",
        "",
        "Date: 2026-09-28",
        "",
        "## Frozen identity",
        "",
        "repository = OpenAutoCoder/Agentless",
        "version = v1.5.0",
        "commit = b150f28465a77a81a7f4776384957a4271f5bd69",
        "",
        "## Native compatibility contract",
        "",
        "Agentless is evaluated as its native repair pipeline, not as a shell agent.",
        "inspect-context -> repair prompt -> OpenAIChatDecoder -> native edit parser -> patch -> CodePro independent verifier",
        "",
        "native shell command loop = NOT_APPLICABLE_AGENTLESS_PIPELINE",
        "",
        "## Frozen local binding",
        "",
        f"endpoint = {(summary.get('local_runtime') or {}).get('base_url')}",
        f"model_alias = {(summary.get('local_runtime') or {}).get('model_alias')}",
        "fallback = DISABLED",
        "",
        "## Result",
        "",
        f"classification = {summary.get('classification')}",
        f"vertical_status = {vertical.get('status')}",
        f"vertical_reason = {vertical.get('reason')}",
        f"model_calls = {telemetry.get('model_calls')}",
        f"prompt_tokens = {telemetry.get('prompt_tokens')}",
        f"completion_tokens = {telemetry.get('completion_tokens')}",
        f"adapter_error = {adapter.get('error')}",
        f"blocker = {summary.get('blocker')}",
        "",
        "## Gates",
        "",
    ]
    for key in sorted(gates):
        lines.append(f"{key.upper()} = {'PASS' if gates.get(key) is True else gates.get(key)}")
    lines.extend([
        "",
        "## Semantics",
        "",
        "S2 classification closes only the Agentless compatibility cell.",
        "A native pipeline difference is recorded rather than hidden by forcing Agentless into an interactive-shell contract.",
        "",
        "AVAILABLE != QUALIFIED",
        "COMPATIBLE != SELECTED",
        "EXECUTED != VERIFIED",
        "VERIFIED != ACCEPTED",
        "NO_SILENT_FALLBACK",
        "NO_SILENT_EXECUTOR_SWITCH",
        "",
        "Evidence: evidence/phase7-scaffold-compatibility/S2-Agentless/.",
        "",
        "Next compatibility cell: S3 AutoCodeRover.",
    ])
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

def update_roadmap(summary: dict) -> None:
    path = ROOT / "roadmap.md"
    text = path.read_text(encoding="utf-8")
    p7 = text.index("## Phase 7")
    p8 = text.index("## Phase 8")
    block = text[p7:p8]
    s2_line_pattern = r"- S2 Agentless: \*\*[^\n]+\."
    replacement = f"- S2 Agentless: **{summary['classification']}** — docs/audits/phase7-s2-agentless-20260928.md."
    if re.search(s2_line_pattern, block):
        block = re.sub(s2_line_pattern, replacement, block, count=1)
    else:
        raise RuntimeError("S2 roadmap cell missing")
    block = re.sub(r"- S3 AutoCodeRover: \*\*[^\n]+\.", "- S3 AutoCodeRover: **NEXT**.", block, count=1)
    block = re.sub(r"\*\*Phase status:\*\* IN_PROGRESS[^\r\n]*", "**Phase status:** IN_PROGRESS — S1/S2 classified; S3 compatibility block next.", block, count=1)
    text = text[:p7] + block + text[p8:]
    text = text.replace("STATUS = IN_PROGRESS / S2_NEXT", "STATUS = IN_PROGRESS / S3_NEXT")
    path.write_text(text, encoding="utf-8", newline="\n")

def repository_gates() -> None:
    run([sys.executable, "tools/check_foundation.py"])
    print("FOUNDATION = PASS")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", ".", "-v"], env=env)
    print("PYTHON_TESTS = PASS")
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if not npm:
        raise RuntimeError("npm executable not found")
    run([npm, "run", "lint"])
    print("NPM_LINT = PASS")
    run([npm, "run", "build"])
    print("NPM_BUILD = PASS")

def main() -> int:
    print("======================================================")
    print(" PHASE 7 - S2 AGENTLESS COMPLETE BLOCK")
    print("======================================================")
    git("fetch", "origin")
    local = git("show-ref", "--verify", "--quiet", f"refs/heads/{BRANCH}", check=False)
    if local.returncode == 0:
        git("switch", BRANCH)
    else:
        git("switch", "-c", BRANCH, "--track", f"origin/{BRANCH}")
    git("pull", "--ff-only", "origin", BRANCH)
    archive_prior()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    run([sys.executable, "tools/run_phase7_s2_agentless.py", "--evidence-dir", str(EVIDENCE)], env=env, timeout=5400)
    summary_path = EVIDENCE / "s2-summary.json"
    if not summary_path.is_file():
        raise RuntimeError("S2 summary missing")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    classification = str(summary.get("classification") or "").strip()
    if not classification:
        raise RuntimeError("S2 classification missing")
    update_manifest(summary)
    write_audit(summary)
    update_roadmap(summary)
    repository_gates()
    roadmap = (ROOT / "roadmap.md").read_text(encoding="utf-8")
    if "STATUS = IN_PROGRESS / S3_NEXT" not in roadmap:
        raise RuntimeError("roadmap did not advance to S3")
    print("ROADMAP_SYNC = PASS")
    git("add", "--", "roadmap.md", "experiments/phase7/scaffold-pool.json", "docs/audits/phase7-s2-agentless-20260928.md", "evidence/phase7-scaffold-compatibility")
    staged = git("diff", "--cached", "--name-only").stdout.splitlines()
    if not staged:
        raise RuntimeError("no S2 closure files staged")
    if any(path.lower().endswith(".gguf") for path in staged):
        raise RuntimeError("GGUF unexpectedly staged")
    authored = [
        "roadmap.md",
        "experiments/phase7/scaffold-pool.json",
        "docs/audits/phase7-s2-agentless-20260928.md",
        "evidence/phase7-scaffold-compatibility/S2-Agentless/s2-summary.json",
        "evidence/phase7-scaffold-compatibility/S2-Agentless/upstream-identity.json",
        "evidence/phase7-scaffold-compatibility/S2-Agentless/installation.json",
        "evidence/phase7-scaffold-compatibility/S2-Agentless/runtime-binding.json",
        "evidence/phase7-scaffold-compatibility/S2-Agentless/server-preflight.json",
        "evidence/phase7-scaffold-compatibility/S2-Agentless/openai-binding-preflight.json",
        "evidence/phase7-scaffold-compatibility/S2-Agentless/agentless-result.json",
    ]
    existing = [path for path in authored if (ROOT / path).exists()]
    git("diff", "--cached", "--check", "--", *existing)
    print("AUTHORED_DIFF_CHECK = PASS")
    head_before = git("rev-parse", "HEAD").stdout.strip()
    git("commit", "-m", "phase7: classify S2 Agentless compatibility")
    head_after = git("rev-parse", "HEAD").stdout.strip()
    if head_after == head_before:
        raise RuntimeError("S2 closure HEAD did not advance")
    git("push", "origin", BRANCH)
    git("fetch", "origin")
    remote_head = git("rev-parse", f"origin/{BRANCH}").stdout.strip()
    if remote_head != head_after:
        raise RuntimeError("remote S2 HEAD mismatch")
    ahead = int(git("rev-list", "--count", f"origin/main..origin/{BRANCH}").stdout.strip())
    gates = summary.get("gates") or {}
    telemetry = summary.get("telemetry") or {}
    vertical = summary.get("vertical") or {}
    print("")
    print("======================================================")
    print(" PHASE 7 - S2 FINAL RESULT")
    print("======================================================")
    print(f"S2_CLASSIFICATION      = {classification}")
    print(f"VERTICAL_STATUS        = {vertical.get('status')}")
    print(f"MODEL_CALLS            = {telemetry.get('model_calls')}")
    print(f"PROMPT_TOKENS          = {telemetry.get('prompt_tokens')}")
    print(f"COMPLETION_TOKENS      = {telemetry.get('completion_tokens')}")
    print(f"EXPLICIT_LOCAL_BINDING = {gates.get('explicit_local_binding')}")
    print(f"INSPECT_OBSERVED       = {gates.get('inspect_observed')}")
    print(f"EDIT_OBSERVED          = {gates.get('edit_observed')}")
    print(f"TERMINATION_OBSERVED   = {gates.get('termination_observed')}")
    print(f"INDEPENDENT_VERIFIER   = {gates.get('independent_verifier')}")
    print("FOUNDATION              = PASS")
    print("PYTHON_TESTS            = PASS")
    print("NPM_LINT                = PASS")
    print("NPM_BUILD               = PASS")
    print("NEXT_CANDIDATE          = S3_AUTOCODEROVER")
    print(f"COMMIT_SHA              = {head_after}")
    print(f"REMOTE_HEAD             = {remote_head}")
    print(f"COMMITS_AHEAD_MAIN      = {ahead}")
    print("NEXT                     = REMOTE_REVIEW_THEN_S3")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
