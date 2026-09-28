#!/usr/bin/env python3
"""Run and close the Phase 7 S3 AutoCodeRover compatibility block."""

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
EVIDENCE = ROOT / "evidence" / "phase7-scaffold-compatibility" / "S3-AutoCodeRover"
DIAGNOSTICS = ROOT / "evidence" / "phase7-scaffold-compatibility" / "diagnostics"
MANIFEST = ROOT / "experiments" / "phase7" / "scaffold-pool.json"
AUDIT = ROOT / "docs" / "audits" / "phase7-s3-autocoderover-20260928.md"

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
    summary_path = EVIDENCE / "s3-summary.json"
    classification = "INCOMPLETE"
    if summary_path.is_file():
        try:
            classification = str(json.loads(summary_path.read_text(encoding="utf-8")).get("classification") or "UNKNOWN")
        except (OSError, json.JSONDecodeError):
            classification = "UNREADABLE"
    DIAGNOSTICS.mkdir(parents=True, exist_ok=True)
    attempt = len([item for item in DIAGNOSTICS.iterdir() if item.is_dir() and item.name.startswith("s3-attempt-")]) + 1
    label = re.sub(r"[^a-z0-9]+", "-", classification.lower()).strip("-") or "unknown"
    while True:
        archive = DIAGNOSTICS / f"s3-attempt-{attempt}-{label}"
        if not archive.exists():
            break
        attempt += 1
    shutil.move(str(EVIDENCE), str(archive))
    print(f"PREVIOUS_S3_ATTEMPT_ARCHIVED = {archive}")

def update_manifest(summary: dict) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    found = False
    for candidate in manifest.get("candidates", []):
        if candidate.get("id") != "S3":
            continue
        found = True
        candidate["phase7_status"] = summary["classification"]
        candidate["evidence"] = "evidence/phase7-scaffold-compatibility/S3-AutoCodeRover/s3-summary.json"
        candidate["observed"] = {
            "vertical_status": (summary.get("vertical") or {}).get("status"),
            "vertical_reason": (summary.get("vertical") or {}).get("reason"),
            "native_contract": summary.get("native_contract"),
            "prompt_tokens": (summary.get("telemetry") or {}).get("prompt_tokens"),
            "completion_tokens": (summary.get("telemetry") or {}).get("completion_tokens"),
            "native_tool_call_count": (summary.get("telemetry") or {}).get("native_tool_call_count"),
            "gates": summary.get("gates"),
            "blocker": summary.get("blocker"),
        }
        break
    if not found:
        raise RuntimeError("S3 candidate missing from manifest")
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

def write_audit(summary: dict) -> None:
    gates = summary.get("gates") or {}
    telemetry = summary.get("telemetry") or {}
    vertical = summary.get("vertical") or {}
    lines = [
        "# Phase 7 S3 - AutoCodeRover compatibility audit",
        "",
        "Date: 2026-09-28",
        "",
        "## Frozen identity",
        "",
        "repository = AutoCodeRoverSG/auto-code-rover",
        "version = v1.1.0",
        "commit = 1aafff1be4549fff4db9d61bf54bfa8b0669ea57",
        "",
        "## Native compatibility contract",
        "",
        "PlainTask -> ProjectApiManager structural search tools -> upstream OpenaiModel tool calls -> write_patch -> extracted patch -> CodePro independent verifier",
        "",
        "The exact upstream requirements are attempted on Windows-native without silently removing Linux/CUDA dependencies.",
        "",
        "## Result",
        "",
        f"classification = {summary.get('classification')}",
        f"vertical_status = {vertical.get('status')}",
        f"vertical_reason = {vertical.get('reason')}",
        f"prompt_tokens = {telemetry.get('prompt_tokens')}",
        f"completion_tokens = {telemetry.get('completion_tokens')}",
        f"native_tool_call_count = {telemetry.get('native_tool_call_count')}",
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
        "S3 classification closes only the AutoCodeRover compatibility cell.",
        "An upstream Windows installation blocker is retained as evidence; dependencies are not silently pruned to manufacture compatibility.",
        "",
        "AVAILABLE != QUALIFIED",
        "COMPATIBLE != SELECTED",
        "INFRA_FAILURE != MODEL_FAILURE",
        "EXECUTED != VERIFIED",
        "VERIFIED != ACCEPTED",
        "NO_SILENT_FALLBACK",
        "NO_SILENT_EXECUTOR_SWITCH",
        "",
        "Evidence: evidence/phase7-scaffold-compatibility/S3-AutoCodeRover/.",
        "",
        "Next compatibility cell: S4 OpenHands.",
    ])
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

def update_roadmap(summary: dict) -> None:
    path = ROOT / "roadmap.md"
    text = path.read_text(encoding="utf-8")
    p7 = text.index("## Phase 7")
    p8 = text.index("## Phase 8")
    block = text[p7:p8]
    if "- S3 AutoCodeRover: **NEXT**." not in block:
        raise RuntimeError("S3 roadmap NEXT cell missing")
    block = block.replace(
        "- S3 AutoCodeRover: **NEXT**.",
        f"- S3 AutoCodeRover: **{summary['classification']}** — docs/audits/phase7-s3-autocoderover-20260928.md.",
    )
    block = re.sub(r"- S4 OpenHands: \*\*[^\n]+\.", "- S4 OpenHands: **NEXT**.", block, count=1)
    block = re.sub(r"\*\*Phase status:\*\* IN_PROGRESS[^\r\n]*", "**Phase status:** IN_PROGRESS — S1/S2/S3 classified; S4 compatibility block next.", block, count=1)
    text = text[:p7] + block + text[p8:]
    text = text.replace("STATUS = IN_PROGRESS / S3_NEXT", "STATUS = IN_PROGRESS / S4_NEXT")
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
    print(" PHASE 7 - S3 AUTOCODEROVER COMPLETE BLOCK")
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
    run([sys.executable, "tools/run_phase7_s3_autocoderover.py", "--evidence-dir", str(EVIDENCE)], env=env, timeout=7200)
    summary_path = EVIDENCE / "s3-summary.json"
    if not summary_path.is_file():
        raise RuntimeError("S3 summary missing")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    classification = str(summary.get("classification") or "").strip()
    if not classification:
        raise RuntimeError("S3 classification missing")
    update_manifest(summary)
    write_audit(summary)
    update_roadmap(summary)
    repository_gates()
    roadmap = (ROOT / "roadmap.md").read_text(encoding="utf-8")
    if "STATUS = IN_PROGRESS / S4_NEXT" not in roadmap:
        raise RuntimeError("roadmap did not advance to S4")
    print("ROADMAP_SYNC = PASS")
    git("add", "--", "roadmap.md", "experiments/phase7/scaffold-pool.json", "docs/audits/phase7-s3-autocoderover-20260928.md", "evidence/phase7-scaffold-compatibility")
    staged = git("diff", "--cached", "--name-only").stdout.splitlines()
    if not staged:
        raise RuntimeError("no S3 closure files staged")
    if any(path.lower().endswith(".gguf") for path in staged):
        raise RuntimeError("GGUF unexpectedly staged")
    authored = [
        "roadmap.md",
        "experiments/phase7/scaffold-pool.json",
        "docs/audits/phase7-s3-autocoderover-20260928.md",
        "evidence/phase7-scaffold-compatibility/S3-AutoCodeRover/s3-summary.json",
        "evidence/phase7-scaffold-compatibility/S3-AutoCodeRover/upstream-identity.json",
        "evidence/phase7-scaffold-compatibility/S3-AutoCodeRover/installation.json",
        "evidence/phase7-scaffold-compatibility/S3-AutoCodeRover/runtime-binding.json",
        "evidence/phase7-scaffold-compatibility/S3-AutoCodeRover/server-preflight.json",
        "evidence/phase7-scaffold-compatibility/S3-AutoCodeRover/autocoderover-result.json",
    ]
    existing = [path for path in authored if (ROOT / path).exists()]
    git("diff", "--cached", "--check", "--", *existing)
    print("AUTHORED_DIFF_CHECK = PASS")
    head_before = git("rev-parse", "HEAD").stdout.strip()
    git("commit", "-m", "phase7: classify S3 AutoCodeRover compatibility")
    head_after = git("rev-parse", "HEAD").stdout.strip()
    if head_after == head_before:
        raise RuntimeError("S3 closure HEAD did not advance")
    git("push", "origin", BRANCH)
    git("fetch", "origin")
    remote_head = git("rev-parse", f"origin/{BRANCH}").stdout.strip()
    if remote_head != head_after:
        raise RuntimeError("remote S3 HEAD mismatch")
    ahead = int(git("rev-list", "--count", f"origin/main..origin/{BRANCH}").stdout.strip())
    gates = summary.get("gates") or {}
    telemetry = summary.get("telemetry") or {}
    vertical = summary.get("vertical") or {}
    print("")
    print("======================================================")
    print(" PHASE 7 - S3 FINAL RESULT")
    print("======================================================")
    print(f"S3_CLASSIFICATION      = {classification}")
    print(f"VERTICAL_STATUS        = {vertical.get('status')}")
    print(f"PROMPT_TOKENS          = {telemetry.get('prompt_tokens')}")
    print(f"COMPLETION_TOKENS      = {telemetry.get('completion_tokens')}")
    print(f"NATIVE_TOOL_CALLS      = {telemetry.get('native_tool_call_count')}")
    print(f"EXACT_REQUIREMENTS     = {gates.get('exact_upstream_requirements')}")
    print(f"LOCAL_RUNTIME_READY    = {gates.get('local_runtime_ready')}")
    print(f"MODEL_CALLS_OBSERVED   = {gates.get('model_calls_observed')}")
    print(f"SEARCH_OBSERVED        = {gates.get('search_observed')}")
    print(f"WRITE_PATCH_OBSERVED   = {gates.get('write_patch_observed')}")
    print(f"EDIT_OBSERVED          = {gates.get('edit_observed')}")
    print(f"INDEPENDENT_VERIFIER   = {gates.get('independent_verifier')}")
    print("FOUNDATION              = PASS")
    print("PYTHON_TESTS            = PASS")
    print("NPM_LINT                = PASS")
    print("NPM_BUILD               = PASS")
    print("NEXT_CANDIDATE          = S4_OPENHANDS")
    print(f"COMMIT_SHA              = {head_after}")
    print(f"REMOTE_HEAD             = {remote_head}")
    print(f"COMMITS_AHEAD_MAIN      = {ahead}")
    print("NEXT                     = REMOTE_REVIEW_THEN_S4")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
