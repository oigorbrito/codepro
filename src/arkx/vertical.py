"""Minimal operational vertical journey for one explicitly selected executor.

This module intentionally implements one narrow path:
authorized request -> immutable Git workspace -> one local-command executor ->
declared verifier -> persisted evidence.

It does not select among executors, invoke a model implicitly, fall back to
another backend, or make an acceptance/promotion decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from typing import Any, Sequence

from .characterization import TaskSignals
from .command import CommandSpec, LocalCommandEnvironment
from .governance import AuthorityGrant, TaskRequest
from .qualification import ExecutorQualification, ExecutorRuntime, QualificationStatus
from .spine import SpineStatus, execute_governed
from .verifier import VerificationEvidenceStore, run_verification_command
from .verification import TestResultStatus


EXECUTOR_ID = "local-command"
EXECUTOR_VERSION = "1"
ADAPTER_ID = "codepro-local-command"
ADAPTER_VERSION = "1"
CAPABILITY_ID = "repository-edit"
QUALIFICATION_EVIDENCE = "local-evidence://command-contract-tests"


class VerticalRunStatus(str, Enum):
    BLOCKED = "BLOCKED"
    EXECUTED = "EXECUTED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    ENVIRONMENT_UNAVAILABLE = "ENVIRONMENT_UNAVAILABLE"


@dataclass(frozen=True)
class VerticalRunResult:
    run_id: str
    status: VerticalRunStatus
    reason: str
    evidence_root: str
    changed_files: tuple[str, ...] = ()
    attempt_id: str = "attempt-1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status.value,
            "reason": self.reason,
            "evidence_root": self.evidence_root,
            "changed_files": list(self.changed_files),
            "attempt_id": self.attempt_id,
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )


class LocalCommandInvoker:
    def __init__(self, workspace: Path, argv: Sequence[str]) -> None:
        if not argv:
            raise ValueError("executor command must be non-empty")
        self.workspace = workspace
        self.argv = tuple(argv)
        self.environment = LocalCommandEnvironment()

    @property
    def identity(self) -> tuple[str, str, str, str]:
        return (EXECUTOR_ID, EXECUTOR_VERSION, ADAPTER_ID, ADAPTER_VERSION)

    def invoke(self, *, timeout_seconds: float, **_: Any):
        return self.environment.execute(
            CommandSpec(
                argv=self.argv,
                cwd=str(self.workspace),
                timeout_seconds=timeout_seconds,
            )
        )


def run_vertical(
    *,
    workspace: str | Path,
    revision: str,
    request_id: str,
    task_id: str,
    requester_ref: str,
    authority_ref: str,
    acceptance_authority_ref: str,
    scope: Sequence[str],
    executor_argv: Sequence[str],
    verifier_argv: Sequence[str],
    evidence_dir: str | Path,
    candidate_files: Sequence[str] | None = None,
    affected_components: Sequence[str] | None = None,
    max_wall_time_seconds: float = 300.0,
    attempt_id: str = "attempt-1",
) -> VerticalRunResult:
    root = Path(workspace).expanduser().resolve()
    evidence_base = Path(evidence_dir).expanduser().resolve()
    if not attempt_id.strip() or Path(attempt_id).name != attempt_id:
        raise ValueError("attempt_id must be a single non-empty path component")
    run_id = _run_id(request_id, attempt_id, revision, tuple(executor_argv), tuple(verifier_argv))
    run_root = evidence_base / run_id

    def finish(status: VerticalRunStatus, reason: str, changed_files: tuple[str, ...] = ()) -> VerticalRunResult:
        result = VerticalRunResult(run_id, status, reason, str(run_root), changed_files, attempt_id)
        _write_new(run_root / "result.json", result.to_dict())
        return result

    if not root.is_dir():
        run_root.mkdir(parents=True, exist_ok=False)
        return finish(VerticalRunStatus.BLOCKED, "WORKSPACE_UNAVAILABLE")

    if evidence_base == root or root in evidence_base.parents:
        raise ValueError("evidence_dir must be outside the target workspace")
    if run_root.exists():
        raise FileExistsError(f"run evidence already exists: {run_root}")

    head = _git(root, "rev-parse", "HEAD")
    if head["returncode"] != 0:
        run_root.mkdir(parents=True)
        _write_new(run_root / "git-head.json", head)
        return finish(VerticalRunStatus.BLOCKED, "GIT_REVISION_UNAVAILABLE")
    actual_revision = head["stdout"].strip()
    if actual_revision != revision:
        run_root.mkdir(parents=True)
        _write_new(run_root / "git-head.json", head)
        return finish(VerticalRunStatus.BLOCKED, "REVISION_MISMATCH")

    initial_status = _git(root, "status", "--porcelain=v1")
    if initial_status["returncode"] != 0:
        run_root.mkdir(parents=True)
        _write_new(run_root / "git-head.json", head)
        _write_new(run_root / "git-status-before.json", initial_status)
        return finish(VerticalRunStatus.BLOCKED, "GIT_STATUS_UNAVAILABLE")
    if initial_status["stdout"].strip():
        run_root.mkdir(parents=True)
        _write_new(run_root / "git-head.json", head)
        _write_new(run_root / "git-status-before.json", initial_status)
        return finish(VerticalRunStatus.BLOCKED, "WORKSPACE_NOT_CLEAN")

    run_root.mkdir(parents=True)
    _write_new(run_root / "git-head.json", head)
    _write_new(run_root / "git-status-before.json", initial_status)

    normalized_scope = tuple(sorted(set(item.replace("\\", "/").strip("/") for item in scope if item.strip())))
    if not normalized_scope:
        return finish(VerticalRunStatus.BLOCKED, "AUTHORIZED_SCOPE_EMPTY")

    normalized_candidates = (
        None
        if candidate_files is None
        else tuple(
            sorted(
                set(
                    item.replace("\\", "/").strip("/")
                    for item in candidate_files
                    if item.strip()
                )
            )
        )
    )
    normalized_components = (
        None
        if affected_components is None
        else tuple(sorted(set(item.strip() for item in affected_components if item.strip())))
    )
    if not normalized_candidates or not normalized_components:
        _write_new(
            run_root / "characterization-input.json",
            {
                "candidate_files": None if normalized_candidates is None else list(normalized_candidates),
                "affected_components": None if normalized_components is None else list(normalized_components),
            },
        )
        return finish(VerticalRunStatus.BLOCKED, "CHARACTERIZATION_REQUIRED")

    outside_candidates = tuple(
        path for path in normalized_candidates if not _within_scope(path, normalized_scope)
    )
    if outside_candidates:
        _write_new(
            run_root / "characterization-input.json",
            {
                "candidate_files": list(normalized_candidates),
                "affected_components": list(normalized_components),
                "outside_authorized_scope": list(outside_candidates),
            },
        )
        return finish(
            VerticalRunStatus.BLOCKED,
            "CHARACTERIZATION_OUTSIDE_AUTHORIZED_SCOPE",
        )

    request = TaskRequest(
        request_id=request_id,
        requester_ref=requester_ref,
        task_ref=task_id,
        project_ref=f"git://{root.as_posix()}@{revision}",
        requested_scope=normalized_scope,
        required_permissions=("edit", "test"),
    )
    grant = AuthorityGrant(
        grant_id=f"{request_id}:grant",
        request_id=request_id,
        authority_ref=authority_ref,
        authorized_scope=normalized_scope,
        permissions=("edit", "test"),
        max_commands=1,
        max_wall_time_seconds=max_wall_time_seconds,
        environment_ref=f"workspace://{root.as_posix()}@{revision}",
        acceptance_authority_ref=acceptance_authority_ref,
        evidence_refs=(f"request://{request_id}",),
    )
    signals = TaskSignals(
        candidate_files=normalized_candidates,
        dependency_edges=(),
        affected_components=normalized_components,
        known_tests=("declared-verifier",),
        ambiguity_markers=(),
        risk_markers=(),
        acceptance_checks=("declared verifier exits zero",),
        state_shared=False,
        architectural_change=False,
    )
    runtime = ExecutorRuntime(
        EXECUTOR_ID,
        EXECUTOR_VERSION,
        ADAPTER_ID,
        ADAPTER_VERSION,
        True,
        f"runtime://{EXECUTOR_ID}/{EXECUTOR_VERSION}",
    )
    qualification = ExecutorQualification(
        EXECUTOR_ID,
        EXECUTOR_VERSION,
        ADAPTER_ID,
        ADAPTER_VERSION,
        CAPABILITY_ID,
        QualificationStatus.QUALIFIED,
        (QUALIFICATION_EVIDENCE,),
    )

    _write_new(run_root / "request.json", request.to_dict())
    _write_new(run_root / "authority-grant.json", grant.to_dict())
    _write_new(run_root / "characterization-input.json", signals.to_dict())

    started_at = time.monotonic()
    record = execute_governed(
        request,
        grant,
        signals,
        capability_id=CAPABILITY_ID,
        runtimes=(runtime,),
        qualifications=(qualification,),
        executor=LocalCommandInvoker(root, executor_argv),
    )
    _write_new(run_root / "execution.json", record.to_dict())

    if record.command_result is None:
        return finish(VerticalRunStatus.BLOCKED, f"EXECUTION_{record.reason.value}")
    if record.reason.value == "COMMAND_TIMEOUT":
        return finish(VerticalRunStatus.TIMED_OUT, "EXECUTION_COMMAND_TIMEOUT")
    if record.reason.value == "ENVIRONMENT_ERROR":
        return finish(VerticalRunStatus.ENVIRONMENT_UNAVAILABLE, "EXECUTION_ENVIRONMENT_ERROR")
    if record.status is not SpineStatus.EXECUTED:
        return finish(VerticalRunStatus.BLOCKED, f"EXECUTION_{record.reason.value}")

    changed_files = _changed_files(root)
    _write_new(run_root / "changed-files.json", {"changed_files": list(changed_files)})
    patch = _workspace_patch(root, revision)
    _write_new(
        run_root / "workspace-patch-summary.json",
        {
            "returncode": patch["returncode"],
            "stderr": patch["stderr"],
            "complete": patch["returncode"] == 0,
        },
    )
    if patch["returncode"] != 0:
        return finish(
            VerticalRunStatus.BLOCKED,
            "WORKSPACE_PATCH_EVIDENCE_UNAVAILABLE",
            changed_files,
        )
    _write_text_new(run_root / "workspace.patch", patch["stdout"])

    outside = tuple(path for path in changed_files if not _within_scope(path, normalized_scope))
    if outside:
        _write_new(run_root / "scope-violation.json", {"outside_scope": list(outside)})
        return finish(VerticalRunStatus.BLOCKED, "CHANGED_FILES_OUTSIDE_AUTHORIZED_SCOPE", changed_files)

    if record.command_result.exit_code != 0:
        return finish(
            VerticalRunStatus.FAILED,
            f"EXECUTOR_EXIT_NONZERO:{record.command_result.exit_code}",
            changed_files,
        )

    if not changed_files:
        return finish(VerticalRunStatus.BLOCKED, "NO_OBSERVABLE_CHANGE")

    if not verifier_argv:
        return finish(VerticalRunStatus.EXECUTED, "VERIFIER_NOT_DECLARED", changed_files)

    elapsed = time.monotonic() - started_at
    remaining_wall_time = max_wall_time_seconds - elapsed
    _write_new(
        run_root / "wall-time-budget.json",
        {
            "max_wall_time_seconds": max_wall_time_seconds,
            "elapsed_before_verifier_seconds": elapsed,
            "remaining_before_verifier_seconds": max(0.0, remaining_wall_time),
        },
    )
    if remaining_wall_time <= 0:
        return finish(
            VerticalRunStatus.TIMED_OUT,
            "TOTAL_WALL_TIME_EXHAUSTED_BEFORE_VERIFIER",
            changed_files,
        )

    observation = run_verification_command(
        tuple(verifier_argv),
        workspace=root,
        test_id=f"{task_id}:declared-verifier",
        required=True,
        timeout_seconds=remaining_wall_time,
    )
    verification_store = VerificationEvidenceStore(run_root / "verification")
    verification_ref = verification_store.persist(run_id, observation)
    _write_new(
        run_root / "verification-summary.json",
        {
            "status": observation.result.status.value,
            "returncode": observation.result.exit_code,
            "duration_ms": observation.result.duration_ms,
            "error_kind": None if observation.error_kind is None else observation.error_kind.value,
            "evidence_ref": verification_ref,
        },
    )

    if observation.result.status is TestResultStatus.PASSED:
        return finish(VerticalRunStatus.VERIFIED, "DECLARED_VERIFIER_PASSED", changed_files)
    if observation.result.status is TestResultStatus.FAILED:
        return finish(VerticalRunStatus.REJECTED, "DECLARED_VERIFIER_FAILED", changed_files)
    return finish(VerticalRunStatus.BLOCKED, "DECLARED_VERIFIER_NOT_EXECUTED_OR_UNKNOWN", changed_files)


def _run_id(
    request_id: str,
    attempt_id: str,
    revision: str,
    executor_argv: tuple[str, ...],
    verifier_argv: tuple[str, ...],
) -> str:
    payload = json.dumps(
        {
            "request_id": request_id,
            "attempt_id": attempt_id,
            "revision": revision,
            "executor_argv": list(executor_argv),
            "verifier_argv": list(verifier_argv),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"{request_id}-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:12]}"


def _git(root: Path, *args: str) -> dict[str, Any]:
    try:
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
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "argv": ["git", "-C", str(root), *args],
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }


def _workspace_patch(root: Path, revision: str) -> dict[str, Any]:
    """Build a complete binary patch without mutating the repository index."""

    with tempfile.TemporaryDirectory(prefix="codepro-index-") as tmp:
        index_path = Path(tmp) / "index"
        environment = os.environ.copy()
        environment["GIT_INDEX_FILE"] = str(index_path)

        read_tree = _git_with_env(root, environment, "read-tree", revision)
        if read_tree["returncode"] != 0:
            return read_tree

        add = _git_with_env(root, environment, "add", "-A", "--", ".")
        if add["returncode"] != 0:
            return add

        return _git_with_env(
            root,
            environment,
            "diff",
            "--cached",
            "--binary",
            "--no-ext-diff",
            revision,
        )


def _git_with_env(root: Path, environment: dict[str, str], *args: str) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            env=environment,
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
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "argv": ["git", "-C", str(root), *args],
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }


def _changed_files(root: Path) -> tuple[str, ...]:
    result = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    if result["returncode"] != 0:
        raise RuntimeError("unable to inspect changed files")

    records = result["stdout"].split("\0")
    paths: list[str] = []
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        if len(record) < 4:
            raise RuntimeError("invalid porcelain status record")

        status = record[:2]
        path = record[3:].replace("\\", "/")
        paths.append(path)

        if "R" in status or "C" in status:
            if index >= len(records) or not records[index]:
                raise RuntimeError("rename/copy status missing source path")
            source = records[index].replace("\\", "/")
            index += 1
            paths.append(source)

    return tuple(sorted(set(paths)))


def _within_scope(path: str, scope: tuple[str, ...]) -> bool:
    normalized = path.replace("\\", "/").strip("/")
    return any(normalized == allowed or normalized.startswith(allowed.rstrip("/") + "/") for allowed in scope)


def _write_new(path: Path, payload: Any) -> None:
    _write_text_new(path, json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def _write_text_new(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"evidence collision: {path}")
    temporary = path.with_name(path.name + f".tmp-{os.getpid()}")
    if temporary.exists():
        raise FileExistsError(f"temporary evidence collision: {temporary}")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    try:
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
