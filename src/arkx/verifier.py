"""Small, executor-neutral verification command boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import subprocess
import time
from collections.abc import Sequence

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
