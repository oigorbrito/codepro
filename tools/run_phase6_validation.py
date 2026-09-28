#!/usr/bin/env python3
"""Run the controlled Phase 6 isolated execution/verifier plumbing validation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).parents[1].resolve()
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from arkx.isolated_workspace import (  # noqa: E402
    IsolatedGitWorkspace,
    capture_repository_state,
)
from arkx.vertical import VerticalRunStatus, run_vertical  # noqa: E402


def run_git(root: Path, *args: str) -> dict[str, Any]:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
        check=False,
        timeout=30,
    )
    return {
        "argv": ["git", "-C", str(root), *args],
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def write_json(path: Path, value: Any) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", required=True)
    args = parser.parse_args(argv)

    evidence_root = Path(args.evidence_dir).expanduser().resolve()
    if evidence_root.exists() and any(evidence_root.iterdir()):
        raise SystemExit(
            f"refusing to overwrite non-empty evidence directory: {evidence_root}"
        )
    evidence_root.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "schema_version": 1,
        "phase": 6,
        "classification": "BLOCKED",
        "model_invoked": False,
        "scaffold_fixture": "PHASE6_CONTROLLED_SCAFFOLD",
        "scaffold_qualified": False,
        "gates": {},
        "vertical": None,
        "operation_kinds": [],
        "telemetry_observed": False,
        "workspace_cleanup": False,
        "next_phase": 7,
    }

    isolated: IsolatedGitWorkspace | None = None
    cleanup_payload: dict[str, Any] | None = None

    try:
        with tempfile.TemporaryDirectory(prefix="codepro-phase6-") as tmp:
            base = Path(tmp)
            source = base / "source"
            workspace_root = base / "workspaces"
            source.mkdir()

            fixture_git = []
            for command in (
                ("init",),
                ("config", "user.email", "phase6@example.invalid"),
                ("config", "user.name", "CodePro Phase 6"),
            ):
                observed = run_git(source, *command)
                fixture_git.append(observed)
                if observed["returncode"] != 0:
                    report["classification"] = "BLOCKED_FIXTURE_GIT"
                    write_json(evidence_root / "phase6-summary.json", report)
                    return 2

            (source / "src").mkdir()
            (source / "src" / "value.txt").write_text(
                "before\n",
                encoding="utf-8",
            )
            for command in (("add", "."), ("commit", "-m", "phase6-base")):
                observed = run_git(source, *command)
                fixture_git.append(observed)
                if observed["returncode"] != 0:
                    report["classification"] = "BLOCKED_FIXTURE_GIT"
                    write_json(evidence_root / "phase6-summary.json", report)
                    return 2

            revision_observation = run_git(source, "rev-parse", "HEAD")
            if revision_observation["returncode"] != 0:
                report["classification"] = "BLOCKED_FIXTURE_REVISION"
                write_json(evidence_root / "phase6-summary.json", report)
                return 2
            revision = revision_observation["stdout"].strip()
            source_before = capture_repository_state(source)

            write_json(
                evidence_root / "fixture-source.json",
                {
                    "fixture_type": "PHASE6_CONTROLLED_REPOSITORY",
                    "git": fixture_git,
                    "revision_observation": revision_observation,
                    "source_state_before": source_before.to_dict(),
                },
            )

            isolated = IsolatedGitWorkspace.create(
                source_repository=source,
                revision=revision,
                workspace_root=workspace_root,
                workspace_id="phase6-task-1",
            )
            write_json(
                evidence_root / "isolated-workspace.json",
                isolated.to_dict(),
            )

            fixture_scaffold = ROOT / "tools" / "phase6_fixture_scaffold.py"
            result = run_vertical(
                workspace=isolated.workspace,
                revision=revision,
                request_id="phase6-controlled-run",
                task_id="phase6-edit-verify",
                requester_ref="user://phase6-validation",
                authority_ref="authority://phase6-validation",
                acceptance_authority_ref="acceptance://phase6-independent-review",
                scope=("src",),
                candidate_files=("src/value.txt",),
                affected_components=("src",),
                characterization_source_ref="evidence://phase6-controlled-fixture",
                executor_argv=(
                    sys.executable,
                    str(fixture_scaffold),
                    "--target",
                    "src/value.txt",
                    "--scope",
                    "src",
                ),
                verifier_argv=(
                    sys.executable,
                    "-c",
                    "from pathlib import Path; "
                    "value=Path('src/value.txt').read_text(encoding='utf-8'); "
                    "print('VERIFIER_OK' if value == 'after\\n' else 'VERIFIER_BAD'); "
                    "raise SystemExit(0 if value == 'after\\n' else 9)",
                ),
                evidence_dir=evidence_root / "vertical",
                max_wall_time_seconds=60,
            )
            run_root = Path(result.evidence_root)
            final_state = isolated.capture_state()
            source_during = capture_repository_state(source)

            execution = json.loads(
                (run_root / "execution.json").read_text(encoding="utf-8")
            )
            command_result = execution.get("command_result") or {}
            stdout = command_result.get("stdout")
            stderr = command_result.get("stderr")
            if not isinstance(stdout, str) or not isinstance(stderr, str):
                raise RuntimeError("execution evidence is missing stdout/stderr")
            operation_payload = json.loads(stdout.strip())
            operations = operation_payload.get("operations")
            if not isinstance(operations, list):
                raise RuntimeError(
                    "fixture scaffold did not emit operation observations"
                )
            operation_kinds = [
                item.get("kind")
                for item in operations
                if isinstance(item, dict)
            ]
            write_json(
                run_root / "operation-observations.json",
                operation_payload,
            )

            patch_path = run_root / "workspace.patch"
            patch_bytes = patch_path.read_bytes()
            patch_sha256 = hashlib.sha256(patch_bytes).hexdigest()
            patch_text = patch_bytes.decode("utf-8", errors="replace")

            verification_summary = json.loads(
                (run_root / "verification-summary.json").read_text(
                    encoding="utf-8"
                )
            )
            verification_files = sorted(
                (run_root / "verification").rglob("verification-*.json")
            )
            if len(verification_files) != 1:
                raise RuntimeError(
                    "expected exactly one persisted verifier evidence file"
                )
            verifier_evidence = json.loads(
                verification_files[0].read_text(encoding="utf-8")
            )

            repository_state = {
                "isolated_workspace": True,
                "requested_revision": revision,
                "initial": isolated.initial_state.to_dict(),
                "final": final_state.to_dict(),
                "source_before": source_before.to_dict(),
                "source_during": source_during.to_dict(),
                "changed_files": list(result.changed_files),
                "workspace_patch_sha256": patch_sha256,
            }
            write_json(
                run_root / "repository-state.json",
                repository_state,
            )

            execution_duration = command_result.get("duration_ms")
            verifier_duration = verification_summary.get("duration_ms")
            telemetry_observed = (
                isinstance(execution_duration, int)
                and execution_duration >= 0
                and isinstance(verifier_duration, int)
                and verifier_duration >= 0
            )

            gates = {
                "isolated_workspace": (
                    isolated.initial_state.clean
                    and isolated.initial_state.revision == revision
                    and isolated.workspace != source
                ),
                "initial_revision_recorded": (
                    isolated.initial_state.revision == revision
                ),
                "inspect_edit_command": (
                    operation_kinds == ["INSPECT", "EDIT", "COMMAND"]
                ),
                "stdout_stderr_captured": (
                    isinstance(stdout, str) and isinstance(stderr, str)
                ),
                "patch_captured": (
                    bool(patch_sha256)
                    and "-before" in patch_text
                    and "+after" in patch_text
                ),
                "tests_commands_captured": (
                    operations[-1].get("stdout", "").strip() == "COMMAND_OK"
                    and verification_summary.get("status") == "PASSED"
                    and verifier_evidence.get("stdout", "").strip()
                    == "VERIFIER_OK"
                ),
                "independent_verifier": (
                    result.status is VerticalRunStatus.VERIFIED
                    and verification_summary.get("status") == "PASSED"
                    and bool(verification_summary.get("evidence_ref"))
                ),
                "verifier_evidence_persisted": verification_files[0].is_file(),
                "final_repository_state": (
                    final_state.revision == revision
                    and not final_state.clean
                    and result.changed_files == ("src/value.txt",)
                ),
                "source_repository_unchanged": source_during.clean,
                "telemetry_observed": telemetry_observed,
            }

            report.update(
                {
                    "vertical": result.to_dict(),
                    "operation_kinds": operation_kinds,
                    "telemetry_observed": telemetry_observed,
                    "gates": gates,
                    "evidence_refs": {
                        "vertical_root": str(
                            run_root.relative_to(evidence_root)
                        ),
                        "patch": str(
                            patch_path.relative_to(evidence_root)
                        ),
                        "verifier": str(
                            verification_files[0].relative_to(evidence_root)
                        ),
                        "repository_state": str(
                            (run_root / "repository-state.json").relative_to(
                                evidence_root
                            )
                        ),
                    },
                }
            )

            cleanup = isolated.remove()
            cleanup_payload = cleanup.to_dict()
            report["workspace_cleanup"] = cleanup.removed
            source_after = capture_repository_state(source)
            report["gates"]["workspace_cleanup"] = cleanup.removed
            report["gates"][
                "source_repository_unchanged_after_cleanup"
            ] = source_after.clean
            write_json(
                evidence_root / "workspace-cleanup.json",
                {
                    **cleanup_payload,
                    "source_state_after": source_after.to_dict(),
                },
            )
            isolated = None

            all_pass = all(report["gates"].values())
            report["classification"] = (
                "PHASE6_EXECUTION_VERIFIER_PASS"
                if all_pass
                else "PHASE6_GATE_FAILED"
            )
            write_json(
                evidence_root / "phase6-summary.json",
                report,
            )
            sys.stdout.write(
                json.dumps(
                    report,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
            return 0 if all_pass else 1
    finally:
        if isolated is not None:
            try:
                cleanup = isolated.remove()
                if cleanup_payload is None:
                    write_json(
                        evidence_root / "workspace-cleanup-on-error.json",
                        cleanup.to_dict(),
                    )
            except Exception as exc:
                error_path = evidence_root / "workspace-cleanup-error.json"
                if not error_path.exists():
                    write_json(
                        error_path,
                        {"error": f"{type(exc).__name__}: {exc}"},
                    )


if __name__ == "__main__":
    raise SystemExit(main())
