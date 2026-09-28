#!/usr/bin/env python3
"""Run and close the Phase 7 S1 mini-SWE-agent compatibility block."""

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
EVIDENCE = ROOT / "evidence" / "phase7-scaffold-compatibility" / "S1-mini-swe-agent"
DIAGNOSTICS = ROOT / "evidence" / "phase7-scaffold-compatibility" / "diagnostics"
MANIFEST = ROOT / "experiments" / "phase7" / "scaffold-pool.json"
AUDIT = ROOT / "docs" / "audits" / "phase7-s1-mini-swe-agent-20260928.md"


def run(argv: list[str], *, env: dict[str, str] | None = None, check: bool = True, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        argv,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
        check=False,
        timeout=timeout,
    )
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
    summary = EVIDENCE / "s1-summary.json"
    classification = "INCOMPLETE"
    if summary.is_file():
        try:
            classification = str(json.loads(summary.read_text(encoding="utf-8")).get("classification") or "UNKNOWN")
        except (OSError, json.JSONDecodeError):
            classification = "UNREADABLE"
    DIAGNOSTICS.mkdir(parents=True, exist_ok=True)
    attempt = len([item for item in DIAGNOSTICS.iterdir() if item.is_dir() and item.name.startswith("s1-attempt-")]) + 1
    label = re.sub(r"[^a-z0-9]+", "-", classification.lower()).strip("-") or "unknown"
    while True:
        archive = DIAGNOSTICS / f"s1-attempt-{attempt}-{label}"
        if not archive.exists():
            break
        attempt += 1
    shutil.move(str(EVIDENCE), str(archive))
    print(f"PREVIOUS_S1_ATTEMPT_ARCHIVED = {archive}")


def update_manifest(summary: dict) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    candidates = manifest.get("candidates")
    if not isinstance(candidates, list):
        raise RuntimeError("Phase 7 manifest candidates missing")
    found = False
    for candidate in candidates:
        if candidate.get("id") != "S1":
            continue
        found = True
        candidate["phase7_status"] = summary["classification"]
        candidate["evidence"] = "evidence/phase7-scaffold-compatibility/S1-mini-swe-agent/s1-summary.json"
        candidate["observed"] = {
            "vertical_status": summary.get("vertical", {}).get("status"),
            "vertical_reason": summary.get("vertical", {}).get("reason"),
            "api_calls": summary.get("telemetry", {}).get("api_calls"),
            "prompt_tokens": summary.get("telemetry", {}).get("prompt_tokens"),
            "completion_tokens": summary.get("telemetry", {}).get("completion_tokens"),
            "mini_exit_status": summary.get("trajectory", {}).get("exit_status"),
            "gates": summary.get("gates"),
        }
        break
    if not found:
        raise RuntimeError("S1 candidate missing from Phase 7 manifest")
    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_audit(summary: dict) -> None:
    gates = summary.get("gates") or {}
    telemetry = summary.get("telemetry") or {}
    trajectory = summary.get("trajectory") or {}
    vertical = summary.get("vertical") or {}
    lines = [
        "# Phase 7 S1 - mini-SWE-agent compatibility audit",
        "",
        "Date: 2026-09-28",
        "",
        "## Frozen identity",
        "",
        "repository = SWE-agent/mini-swe-agent",
        "version = v2.4.6",
        "commit = a83fcae82d2a08f0ee0c688f9d137b3566c097f8",
        "",
        "## Frozen local binding",
        "",
        f"endpoint = {summary['local_runtime']['base_url']}",
        f"model_alias = {summary['local_runtime']['model_alias']}",
        "fallback = DISABLED",
        "",
        "## Result",
        "",
        f"classification = {summary['classification']}",
        f"vertical_status = {vertical.get('status')}",
        f"vertical_reason = {vertical.get('reason')}",
        f"mini_exit_status = {trajectory.get('exit_status')}",
        f"api_calls = {telemetry.get('api_calls')}",
        f"prompt_tokens = {telemetry.get('prompt_tokens')}",
        f"completion_tokens = {telemetry.get('completion_tokens')}",
        f"instance_cost = {telemetry.get('instance_cost')}",
        "",
        "## Candidate gates",
        "",
    ]
    for key in (
        "exact_upstream_identity",
        "installed_version",
        "local_runtime_ready",
        "model_calls_observed",
        "inspect_observed",
        "command_observed",
        "edit_observed",
        "termination_observed",
        "patch_captured",
        "independent_verifier",
        "source_repository_unchanged",
        "workspace_cleanup",
    ):
        lines.append(f"{key.upper()} = {'PASS' if gates.get(key) else 'NO'}")
    lines.extend([
        "",
        "## Semantics",
        "",
        "S1 classification closes only the mini-SWE-agent compatibility cell.",
        "It does not rank, select, accept, or promote a scaffold.",
        "",
        "AVAILABLE != QUALIFIED",
        "COMPATIBLE != SELECTED",
        "EXECUTED != VERIFIED",
        "VERIFIED != ACCEPTED",
        "NO_SILENT_FALLBACK",
        "NO_SILENT_EXECUTOR_SWITCH",
        "",
        "If the classification is BLOCKED_MODEL_TOOL_PROTOCOL, the observed blocker belongs to the frozen model/server tool-call protocol and must not be rewritten as a mini-SWE-agent implementation failure.",
        "",
        "Prior diagnostic: the first interactive-CLI attempt was invalidated before the first model call by prompt_toolkit NoConsoleScreenBufferError under captured Windows stdout/stderr. That attempt is preserved under diagnostics and is not a compatibility result.",
        "",
        "Evidence: evidence/phase7-scaffold-compatibility/S1-mini-swe-agent/.",
        "",
        "Next compatibility cell: S2 Agentless.",
    ])
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def update_roadmap(summary: dict) -> None:
    path = ROOT / "roadmap.md"
    text = path.read_text(encoding="utf-8")
    p7 = text.index("## Phase 7")
    p8 = text.index("## Phase 8")
    block = text[p7:p8]
    status_section = (
        "Candidate compatibility cells:\n\n"
        f"- S1 mini-swe-agent v2.4.6: **{summary['classification']}** - docs/audits/phase7-s1-mini-swe-agent-20260928.md.\n"
        "- S2 Agentless: **NEXT**.\n"
        "- S3 AutoCodeRover: **NOT_STARTED**.\n"
        "- S4 OpenHands: **NOT_STARTED**.\n\n"
    )
    if "Candidate compatibility cells:" in block:
        start = block.index("Candidate compatibility cells:")
        phase_status = block.index("**Phase status:**", start)
        block = block[:start] + status_section + block[phase_status:]
        block = re.sub(
            r"\*\*Phase status:\*\*[^\r\n]*",
            "**Phase status:** IN_PROGRESS - S1 classified; S2 compatibility block next.",
            block,
            count=1,
        )
    else:
        marker = "**Phase status:** IN_PROGRESS — pool frozen; S1 compatibility block next."
        if marker not in block:
            marker = "**Phase status:** IN_PROGRESS - pool frozen; S1 compatibility block next."
        if marker not in block:
            raise RuntimeError("Phase 7 status marker missing")
        block = block.replace(
            marker,
            status_section + "**Phase status:** IN_PROGRESS - S1 classified; S2 compatibility block next.",
        )
    text = text[:p7] + block + text[p8:]
    text = text.replace(
        "PHASE 7 = SCAFFOLD COMPATIBILITY\nSTATUS = IN_PROGRESS / S1_NEXT",
        "PHASE 7 = SCAFFOLD COMPATIBILITY\nSTATUS = IN_PROGRESS / S2_NEXT",
    )
    text = text.replace(
        "PHASE 7 = SCAFFOLD COMPATIBILITY\nSTATUS = IN_PROGRESS / S1_HEADLESS_RETEST",
        "PHASE 7 = SCAFFOLD COMPATIBILITY\nSTATUS = IN_PROGRESS / S2_NEXT",
    )
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
    print(" PHASE 7 - S1 MINI-SWE-AGENT COMPLETE BLOCK")
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
    run(
        [sys.executable, "tools/run_phase7_s1_mini.py", "--evidence-dir", str(EVIDENCE)],
        env=env,
        timeout=3600,
    )

    summary_path = EVIDENCE / "s1-summary.json"
    if not summary_path.is_file():
        raise RuntimeError("S1 summary was not produced")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    classification = str(summary.get("classification") or "").strip()
    if not classification:
        raise RuntimeError("S1 classification missing")

    update_manifest(summary)
    write_audit(summary)
    update_roadmap(summary)
    repository_gates()

    roadmap = (ROOT / "roadmap.md").read_text(encoding="utf-8")
    if "STATUS = IN_PROGRESS / S2_NEXT" not in roadmap:
        raise RuntimeError("roadmap did not advance to S2")
    print("ROADMAP_SYNC = PASS")

    git("add", "--", "roadmap.md", "experiments/phase7/scaffold-pool.json", "docs/audits/phase7-s1-mini-swe-agent-20260928.md", "evidence/phase7-scaffold-compatibility")
    staged = git("diff", "--cached", "--name-only").stdout.splitlines()
    if not staged:
        raise RuntimeError("no S1 closure files staged")
    if any(path.lower().endswith(".gguf") for path in staged):
        raise RuntimeError("GGUF unexpectedly staged")

    authored = [
        "roadmap.md",
        "experiments/phase7/scaffold-pool.json",
        "docs/audits/phase7-s1-mini-swe-agent-20260928.md",
        "evidence/phase7-scaffold-compatibility/S1-mini-swe-agent/upstream-identity.json",
        "evidence/phase7-scaffold-compatibility/S1-mini-swe-agent/installation.json",
        "evidence/phase7-scaffold-compatibility/S1-mini-swe-agent/runtime-binding.json",
        "evidence/phase7-scaffold-compatibility/S1-mini-swe-agent/server-preflight.json",
        "evidence/phase7-scaffold-compatibility/S1-mini-swe-agent/s1-summary.json",
    ]
    existing_authored = [path for path in authored if (ROOT / path).exists()]
    git("diff", "--cached", "--check", "--", *existing_authored)
    print("AUTHORED_DIFF_CHECK = PASS")

    head_before = git("rev-parse", "HEAD").stdout.strip()
    git("commit", "-m", "phase7: classify S1 mini-swe-agent compatibility")
    head_after = git("rev-parse", "HEAD").stdout.strip()
    if head_after == head_before:
        raise RuntimeError("S1 closure HEAD did not advance")
    git("push", "origin", BRANCH)
    git("fetch", "origin")
    remote_head = git("rev-parse", f"origin/{BRANCH}").stdout.strip()
    if remote_head != head_after:
        raise RuntimeError("remote S1 HEAD mismatch")
    ahead = int(git("rev-list", "--count", f"origin/main..origin/{BRANCH}").stdout.strip())

    print("")
    print("======================================================")
    print(" PHASE 7 - S1 FINAL RESULT")
    print("======================================================")
    print(f"S1_CLASSIFICATION      = {classification}")
    print(f"VERTICAL_STATUS        = {summary.get('vertical', {}).get('status')}")
    print(f"MINI_EXIT_STATUS       = {summary.get('trajectory', {}).get('exit_status')}")
    print(f"MODEL_CALLS            = {summary.get('telemetry', {}).get('api_calls')}")
    print(f"PROMPT_TOKENS          = {summary.get('telemetry', {}).get('prompt_tokens')}")
    print(f"COMPLETION_TOKENS      = {summary.get('telemetry', {}).get('completion_tokens')}")
    print(f"INSPECT_OBSERVED       = {summary.get('gates', {}).get('inspect_observed')}")
    print(f"EDIT_OBSERVED          = {summary.get('gates', {}).get('edit_observed')}")
    print(f"COMMAND_OBSERVED       = {summary.get('gates', {}).get('command_observed')}")
    print(f"TERMINATION_OBSERVED   = {summary.get('gates', {}).get('termination_observed')}")
    print(f"INDEPENDENT_VERIFIER   = {summary.get('gates', {}).get('independent_verifier')}")
    print("FOUNDATION              = PASS")
    print("PYTHON_TESTS            = PASS")
    print("NPM_LINT                = PASS")
    print("NPM_BUILD               = PASS")
    print("NEXT_CANDIDATE          = S2_AGENTLESS")
    print(f"COMMIT_SHA              = {head_after}")
    print(f"REMOTE_HEAD             = {remote_head}")
    print(f"COMMITS_AHEAD_MAIN      = {ahead}")
    print("NEXT                     = REMOTE_REVIEW_THEN_S2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
