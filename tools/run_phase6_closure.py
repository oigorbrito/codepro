#!/usr/bin/env python3
"""Close Phase 6 with one controlled validation, repository gates, commit, and push."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).parents[1].resolve()
BRANCH = "phase6/execution-verifier-plumbing"
EVIDENCE = ROOT / "evidence" / "phase6-execution-verifier" / "controlled-smoke"
DIAGNOSTICS = ROOT / "evidence" / "phase6-execution-verifier" / "diagnostics"
AUDIT = ROOT / "docs" / "audits" / "phase6-execution-verifier-plumbing-20260928.md"


def run(
    argv: list[str],
    *,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
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
    )
    if completed.stdout:
        sys.stdout.write(completed.stdout)
    if completed.stderr:
        sys.stderr.write(completed.stderr)
    if check and completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {argv!r}"
        )
    return completed


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], check=check)


def archive_prior_evidence() -> None:
    if not EVIDENCE.exists():
        return
    classification = "INCOMPLETE"
    summary = EVIDENCE / "phase6-summary.json"
    if summary.is_file():
        try:
            classification = str(
                json.loads(
                    summary.read_text(encoding="utf-8")
                ).get("classification")
                or "UNKNOWN"
            )
        except (OSError, json.JSONDecodeError):
            classification = "UNREADABLE"
    if classification == "PHASE6_EXECUTION_VERIFIER_PASS":
        raise RuntimeError(
            "existing Phase 6 evidence is already PASS; refusing overwrite"
        )

    DIAGNOSTICS.mkdir(parents=True, exist_ok=True)
    attempt = len(
        [item for item in DIAGNOSTICS.iterdir() if item.is_dir()]
    ) + 1
    label = (
        re.sub(r"[^a-z0-9]+", "-", classification.lower()).strip("-")
        or "unknown"
    )
    while True:
        archive = DIAGNOSTICS / f"attempt-{attempt}-{label}"
        if not archive.exists():
            break
        attempt += 1
    shutil.move(str(EVIDENCE), str(archive))
    print(f"PREVIOUS_ATTEMPT_ARCHIVED = {archive}")


def require_summary() -> dict[str, Any]:
    summary = json.loads(
        (EVIDENCE / "phase6-summary.json").read_text(encoding="utf-8")
    )
    if summary.get("classification") != "PHASE6_EXECUTION_VERIFIER_PASS":
        raise RuntimeError(
            f"unexpected Phase 6 classification: "
            f"{summary.get('classification')}"
        )
    required = (
        "isolated_workspace",
        "initial_revision_recorded",
        "inspect_edit_command",
        "stdout_stderr_captured",
        "patch_captured",
        "tests_commands_captured",
        "independent_verifier",
        "verifier_evidence_persisted",
        "final_repository_state",
        "source_repository_unchanged",
        "telemetry_observed",
        "workspace_cleanup",
        "source_repository_unchanged_after_cleanup",
    )
    gates = summary.get("gates") or {}
    failed = [name for name in required if gates.get(name) is not True]
    if failed:
        raise RuntimeError(f"Phase 6 gates failed: {failed}")
    return summary


def write_audit(summary: dict[str, Any]) -> None:
    vertical = summary["vertical"]
    lines = [
        "# Phase 6 - Execution and verifier plumbing audit",
        "",
        "Date: 2026-09-28",
        "",
        "## Result",
        "",
        f"classification: {summary['classification']}",
        f"controlled scaffold fixture: {summary['scaffold_fixture']}",
        f"scaffold qualified: {str(summary['scaffold_qualified']).lower()}",
        f"model invoked: {str(summary['model_invoked']).lower()}",
        f"vertical status: {vertical['status']}",
        f"vertical reason: {vertical['reason']}",
        f"operations: {', '.join(summary['operation_kinds'])}",
        f"telemetry observed: {str(summary['telemetry_observed']).lower()}",
        f"workspace cleanup: {str(summary['workspace_cleanup']).lower()}",
        "",
        "## Gate",
        "",
        "ISOLATED_WORKSPACE = PASS",
        "INITIAL_REVISION = PASS",
        "INSPECT_EDIT_COMMAND = PASS",
        "STDOUT_STDERR = PASS",
        "PATCH_CAPTURE = PASS",
        "TESTS_COMMANDS = PASS",
        "INDEPENDENT_VERIFIER = PASS",
        "VERIFIER_EVIDENCE = PASS",
        "FINAL_REPOSITORY_STATE = PASS",
        "SOURCE_REPOSITORY_UNCHANGED = PASS",
        "TELEMETRY_OBSERVED = PASS",
        "WORKSPACE_CLEANUP = PASS",
        "",
        "## Semantics",
        "",
        "CONTROLLED_SCAFFOLD_FIXTURE != QUALIFIED_SCAFFOLD",
        "MODEL_NOT_INVOKED != MODEL_FAILURE",
        "EXECUTED != VERIFIED",
        "VERIFIED != ACCEPTED",
        "ACCEPTED != PROMOTED",
        "",
        (
            "Phase 6 validates generic plumbing only. Phase 7 owns real "
            "scaffold-to-local-runtime compatibility."
        ),
        "",
        "Evidence: `evidence/phase6-execution-verifier/controlled-smoke/`.",
        "",
        "Next: Phase 7 - scaffold compatibility.",
    ]
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def update_docs() -> None:
    roadmap_path = ROOT / "roadmap.md"
    roadmap = roadmap_path.read_text(encoding="utf-8")
    p6 = roadmap.index("## Phase 6")
    p7 = roadmap.index("## Phase 7")
    phase6 = roadmap[p6:p7]
    phase6 = re.sub(r"(?m)^- \[ \] ", "- [x] ", phase6)
    phase6 = re.sub(
        r"\*\*Phase status:\*\* IN_PROGRESS[^\r\n]*",
        (
            "**Evidence:** "
            "`docs/audits/phase6-execution-verifier-plumbing-20260928.md`."
            "\n\n**Phase status:** COMPLETE"
        ),
        phase6,
    )
    roadmap = roadmap[:p6] + phase6 + roadmap[p7:]
    roadmap = roadmap.replace(
        "PHASE 6   Execution/verifier plumbing   IN_PROGRESS",
        "PHASE 6   Execution/verifier plumbing   COMPLETE",
    )
    roadmap = re.sub(
        (
            r"PHASE 6 = EXECUTION AND VERIFIER PLUMBING\r?\n"
            r"STATUS = IN_PROGRESS / CONTROLLED_VALIDATION_PENDING"
        ),
        "PHASE 7 = SCAFFOLD COMPATIBILITY\nSTATUS = NEXT",
        roadmap,
    )
    roadmap_path.write_text(
        roadmap,
        encoding="utf-8",
        newline="\n",
    )

    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    readme = readme.replace(
        "CURRENT PHASE = PHASE 6 / EXECUTION AND VERIFIER PLUMBING",
        "CURRENT PHASE = PHASE 7 / SCAFFOLD COMPATIBILITY",
    )
    heading = "### Phase 6 execution/verifier closure"
    if heading not in readme:
        anchor = "See [roadmap.md](roadmap.md)."
        if anchor not in readme:
            raise RuntimeError("README roadmap anchor missing")
        section = "\n".join(
            [
                heading,
                "",
                (
                    "The generic execution/verifier plumbing passed a "
                    "controlled isolated-worktree validation:"
                ),
                "",
                (
                    "`CodePro -> controlled scaffold fixture -> isolated "
                    "repository -> patch -> command/test -> independent "
                    "verifier -> persisted final state/telemetry`."
                ),
                "",
                (
                    "The fixture is not a qualified scaffold and no model "
                    "was invoked; Phase 7 owns real scaffold compatibility "
                    "against the Phase 5 local runtime."
                ),
                "",
                (
                    "Evidence: [Phase 6 execution/verifier audit]"
                    "(docs/audits/"
                    "phase6-execution-verifier-plumbing-20260928.md)."
                ),
                "",
            ]
        )
        readme = readme.replace(anchor, section + "\n" + anchor)
    readme_path.write_text(
        readme,
        encoding="utf-8",
        newline="\n",
    )


def repository_gates() -> None:
    run([sys.executable, "tools/check_foundation.py"])
    print("FOUNDATION = PASS")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-t",
            ".",
            "-v",
        ],
        env=env,
    )
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
    print(" PHASE 6 - EXECUTION / VERIFIER COMPLETE CLOSURE")
    print("======================================================")

    git("fetch", "origin")
    local_branch = git(
        "show-ref",
        "--verify",
        "--quiet",
        f"refs/heads/{BRANCH}",
        check=False,
    )
    if local_branch.returncode == 0:
        git("switch", BRANCH)
    else:
        git("switch", "-c", BRANCH, "--track", f"origin/{BRANCH}")
    git("pull", "--ff-only", "origin", BRANCH)

    archive_prior_evidence()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    run(
        [
            sys.executable,
            "tools/run_phase6_validation.py",
            "--evidence-dir",
            str(EVIDENCE),
        ],
        env=env,
    )
    summary = require_summary()

    print("ISOLATED_WORKSPACE      = PASS")
    print("INITIAL_REVISION        = PASS")
    print("INSPECT_EDIT_COMMAND    = PASS")
    print("STDOUT_STDERR           = PASS")
    print("PATCH_CAPTURE           = PASS")
    print("INDEPENDENT_VERIFIER    = PASS")
    print("FINAL_REPOSITORY_STATE  = PASS")
    print("WORKSPACE_CLEANUP       = PASS")

    write_audit(summary)
    update_docs()
    repository_gates()

    roadmap = (ROOT / "roadmap.md").read_text(encoding="utf-8")
    if "PHASE 6   Execution/verifier plumbing   COMPLETE" not in roadmap:
        raise RuntimeError("roadmap did not mark Phase 6 complete")
    if "PHASE 7 = SCAFFOLD COMPATIBILITY" not in roadmap:
        raise RuntimeError("roadmap did not advance to Phase 7")
    print("ROADMAP_SYNC = PASS")

    git(
        "add",
        "--",
        "README.md",
        "roadmap.md",
        "docs/audits/phase6-execution-verifier-plumbing-20260928.md",
        "evidence/phase6-execution-verifier",
    )
    staged = git("diff", "--cached", "--name-only").stdout.splitlines()
    if not staged:
        raise RuntimeError("no Phase 6 closure files staged")
    if any(path.lower().endswith(".gguf") for path in staged):
        raise RuntimeError("GGUF unexpectedly staged")
    git("diff", "--cached", "--check")
    print("STAGED_DIFF_CHECK = PASS")

    head_before = git("rev-parse", "HEAD").stdout.strip()
    git("commit", "-m", "phase6: close execution verifier plumbing")
    head_after = git("rev-parse", "HEAD").stdout.strip()
    if head_after == head_before:
        raise RuntimeError("closure HEAD did not advance")

    git("push", "origin", BRANCH)
    git("fetch", "origin")
    remote_head = git("rev-parse", f"origin/{BRANCH}").stdout.strip()
    if remote_head != head_after:
        raise RuntimeError("remote Phase 6 HEAD mismatch")
    ahead = int(
        git(
            "rev-list",
            "--count",
            f"origin/main..origin/{BRANCH}",
        ).stdout.strip()
    )
    if ahead < 2:
        raise RuntimeError(
            "expected implementation + closure commits ahead of main"
        )

    print("")
    print("======================================================")
    print(" PHASE 6 - FINAL RESULT")
    print("======================================================")
    print("ISOLATED_WORKSPACE     = PASS")
    print("INITIAL_REVISION       = PASS")
    print("INSPECT_EDIT_COMMAND   = PASS")
    print("STDOUT_STDERR          = PASS")
    print("PATCH_CAPTURE          = PASS")
    print("TESTS_COMMANDS         = PASS")
    print("INDEPENDENT_VERIFIER   = PASS")
    print("VERIFIER_EVIDENCE      = PASS")
    print("FINAL_REPOSITORY_STATE = PASS")
    print("TELEMETRY_OBSERVED     = PASS")
    print("WORKSPACE_CLEANUP      = PASS")
    print("FOUNDATION             = PASS")
    print("PYTHON_TESTS           = PASS")
    print("NPM_LINT               = PASS")
    print("NPM_BUILD              = PASS")
    print("PHASE6                 = COMPLETE")
    print("NEXT_PHASE             = PHASE7")
    print(f"COMMIT_SHA             = {head_after}")
    print(f"REMOTE_HEAD            = {remote_head}")
    print(f"COMMITS_AHEAD_MAIN     = {ahead}")
    print("NEXT                    = REMOTE_PR_ACCEPTANCE_AND_MERGE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
