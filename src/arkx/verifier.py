"""Small, executor-neutral verification command boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from collections.abc import Sequence

from .outcomes import VerificationResult, VerificationState
from .verification import TestResult, TestResultStatus


class VerificationErrorKind(str, Enum):
    TIMEOUT = "TIMEOUT"
    EXECUTABLE_NOT_FOUND = "EXECUTABLE_NOT_FOUND"
    INVOCATION_ERROR = "INVOCATION_ERROR"


@dataclass(frozen=True)
class VerificationObservation:
    result: TestResult
    stdout: str
    stderr: str
    error_kind: VerificationErrorKind | None = None


class VerificationEvidenceStore:
    """Persist raw verifier observations without silently replacing attempts."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def has_run(self, run_id: str) -> bool:
        """Return whether evidence for this verifier run already exists."""
        if not run_id.strip() or Path(run_id).name != run_id:
            raise ValueError("run_id must be a single non-empty path component")
        run_root = (self.root / run_id).resolve()
        if self.root not in run_root.parents:
            raise ValueError("verification evidence path escapes store root")
        return run_root.is_dir() and any(run_root.glob("verification-*.json"))

    def persist(self, run_id: str, observation: VerificationObservation) -> str:
        if not run_id.strip() or Path(run_id).name != run_id:
            raise ValueError("run_id must be a single non-empty path component")
        payload = {
            "run_id": run_id,
            "result": observation.result.to_dict(),
            "stdout": observation.stdout,
            "stderr": observation.stderr,
            "error_kind": None if observation.error_kind is None else observation.error_kind.value,
        }
        content = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        identity = json.dumps({"run_id": run_id, "test_id": observation.result.test_id}, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
        target = (self.root / run_id / f"verification-{digest}.json").resolve()
        if self.root not in target.parents:
            raise ValueError("verification evidence path escapes store root")
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.read_text(encoding="utf-8") != content:
                raise FileExistsError(f"verification evidence collision: {target}")
            return f"evidence://{target.relative_to(self.root).as_posix()}"
        temporary = target.with_name(target.name + f".tmp-{os.getpid()}")
        if temporary.exists():
            raise FileExistsError(f"temporary verification evidence already exists: {temporary}")
        temporary.write_text(content, encoding="utf-8", newline="\n")
        try:
            if target.exists():
                if target.read_text(encoding="utf-8") != content:
                    raise FileExistsError(f"verification evidence collision: {target}")
            else:
                temporary.replace(target)
        finally:
            if temporary.exists():
                temporary.unlink()
        return f"evidence://{target.relative_to(self.root).as_posix()}"


class CommandVerifier:
    """Adapt one declared local verifier command to the orchestration seam."""

    def __init__(
        self,
        *,
        authority: str,
        workspace: str | Path,
        command: Sequence[str],
        test_id: str,
        evidence_store: VerificationEvidenceStore,
        required: bool = True,
        timeout_seconds: float = 30.0,
    ) -> None:
        if not authority.strip():
            raise ValueError("authority must be non-empty")
        self.authority = authority
        self.workspace = workspace
        self.command = tuple(command)
        self.test_id = test_id
        self.evidence_store = evidence_store
        self.required = required
        self.timeout_seconds = timeout_seconds

    def verify(self, execution) -> VerificationResult:
        if getattr(execution.outcome, "value", execution.outcome) != "COMPLETED":
            return VerificationResult(VerificationState.NOT_EXECUTED, self.authority, (), ("execution-not-completed",), ())
        has_run = getattr(self.evidence_store, "has_run", None)
        if has_run is not None and has_run(execution.run_id):
            return VerificationResult(
                VerificationState.BLOCKED,
                self.authority,
                (),
                ("verifier-run-id-already-used",),
                (),
            )
        observation = run_verification_command(
            self.command,
            workspace=self.workspace,
            test_id=self.test_id,
            required=self.required,
            timeout_seconds=self.timeout_seconds,
        )
        try:
            evidence_ref = self.evidence_store.persist(execution.run_id, observation)
        except (OSError, ValueError, FileExistsError) as error:
            return VerificationResult(
                VerificationState.BLOCKED,
                self.authority,
                (" ".join(self.command),),
                (f"evidence-persistence-error:{type(error).__name__}",),
                (),
            )
        state = {
            TestResultStatus.PASSED: VerificationState.PASS,
            TestResultStatus.FAILED: VerificationState.FAIL,
            TestResultStatus.UNKNOWN: VerificationState.INDETERMINATE,
            TestResultStatus.NOT_EXECUTED: VerificationState.NOT_EXECUTED,
        }[observation.result.status]
        return VerificationResult(
            state,
            self.authority,
            (" ".join(self.command),),
            (f"{self.test_id}:{observation.result.status.value}",),
            (evidence_ref,),
        )


def run_verification_command(
    command: Sequence[str],
    *,
    workspace: str | Path,
    test_id: str,
    required: bool = True,
    timeout_seconds: float = 30.0,
    evidence_ref: str | None = None,
) -> VerificationObservation:
    """Run one declared verifier command without shell interpretation."""

    argv = tuple(command)
    if not argv or any(not item.strip() for item in argv):
        raise ValueError("verification command must contain non-empty argv items")
    if not test_id.strip():
        raise ValueError("test_id must be non-empty")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    root = Path(workspace).resolve()
    if not root.is_dir():
        raise ValueError("verification workspace must be an existing directory")

    started = time.monotonic()
    try:
        completed = subprocess.run(
            list(argv),
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            shell=False,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        duration_ms = int((time.monotonic() - started) * 1000)
        result = TestResult(test_id, TestResultStatus.UNKNOWN, required, evidence_ref, argv, None, duration_ms)
        return VerificationObservation(result, _text(error.stdout), _text(error.stderr), VerificationErrorKind.TIMEOUT)
    except FileNotFoundError as error:
        duration_ms = int((time.monotonic() - started) * 1000)
        result = TestResult(test_id, TestResultStatus.UNKNOWN, required, evidence_ref, argv, None, duration_ms)
        return VerificationObservation(result, "", str(error), VerificationErrorKind.EXECUTABLE_NOT_FOUND)
    except OSError as error:
        duration_ms = int((time.monotonic() - started) * 1000)
        result = TestResult(test_id, TestResultStatus.UNKNOWN, required, evidence_ref, argv, None, duration_ms)
        return VerificationObservation(result, "", str(error), VerificationErrorKind.INVOCATION_ERROR)

    duration_ms = int((time.monotonic() - started) * 1000)
    status = TestResultStatus.PASSED if completed.returncode == 0 else TestResultStatus.FAILED
    result = TestResult(test_id, status, required, evidence_ref, argv, completed.returncode, duration_ms)
    return VerificationObservation(result, completed.stdout, completed.stderr)


def _text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value
