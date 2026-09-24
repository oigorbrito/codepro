"""Benchmark-informed local command execution primitive.

This module observes process execution. It does not infer task success,
verification, acceptance, or promotion.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from math import isfinite
import os
from pathlib import Path
import signal
import subprocess
import time
from typing import Any, Mapping, Protocol


SCHEMA_VERSION = 1


class EnvironmentErrorKind(str, Enum):
    CWD_UNAVAILABLE = "CWD_UNAVAILABLE"
    EXECUTABLE_NOT_FOUND = "EXECUTABLE_NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    OS_ERROR = "OS_ERROR"
    TERMINATION_ERROR = "TERMINATION_ERROR"


@dataclass(frozen=True)
class CommandEnvironmentError:
    kind: EnvironmentErrorKind
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, EnvironmentErrorKind):
            raise ValueError("kind must be an EnvironmentErrorKind")
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("environment error message must be non-empty")

    def to_dict(self) -> dict[str, str]:
        return {"kind": self.kind.value, "message": self.message}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "CommandEnvironmentError":
        if not isinstance(value, Mapping):
            raise ValueError("environment error must be a mapping")
        kind = value.get("kind")
        message = value.get("message")
        if not isinstance(kind, str):
            raise ValueError("environment error kind must be a string")
        if not isinstance(message, str):
            raise ValueError("environment error message must be a string")
        return cls(EnvironmentErrorKind(kind), message)


@dataclass(frozen=True)
class CommandSpec:
    argv: tuple[str, ...]
    cwd: str
    timeout_seconds: float = 30.0
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.argv, tuple) or not self.argv:
            raise ValueError("argv must be a non-empty tuple")
        if not isinstance(self.argv[0], str) or not self.argv[0].strip():
            raise ValueError("argv[0] must name a non-empty executable")
        if any(not isinstance(item, str) for item in self.argv):
            raise ValueError("argv must contain only strings")
        if any("\x00" in item for item in self.argv):
            raise ValueError("argv cannot contain NUL bytes")
        if not isinstance(self.cwd, str) or not self.cwd.strip():
            raise ValueError("cwd must be a non-empty string")
        if "\x00" in self.cwd:
            raise ValueError("cwd cannot contain NUL bytes")
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
            or not isfinite(float(self.timeout_seconds))
            or self.timeout_seconds <= 0
        ):
            raise ValueError("timeout_seconds must be a finite positive number")
        if isinstance(self.schema_version, bool) or self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported command spec schema: {self.schema_version}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "argv": list(self.argv),
            "cwd": self.cwd,
            "timeout_seconds": self.timeout_seconds,
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "CommandSpec":
        if not isinstance(value, Mapping):
            raise ValueError("command spec must be a mapping")
        schema_version = value.get("schema_version", 0)
        if isinstance(schema_version, bool) or not isinstance(schema_version, int):
            raise ValueError("schema_version must be an integer")
        argv = value.get("argv")
        cwd = value.get("cwd")
        timeout = value.get("timeout_seconds")
        if not isinstance(argv, list):
            raise ValueError("argv must be a list")
        if not isinstance(cwd, str):
            raise ValueError("cwd must be a string")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            raise ValueError("timeout_seconds must be numeric")
        return cls(
            argv=tuple(argv),
            cwd=cwd,
            timeout_seconds=float(timeout),
            schema_version=schema_version,
        )

    @classmethod
    def from_json(cls, value: str) -> "CommandSpec":
        return cls.from_dict(json.loads(value))


@dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    cwd: str
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool
    duration_ms: int
    environment_error: CommandEnvironmentError | None = None
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.argv, tuple) or not self.argv:
            raise ValueError("argv must be a non-empty tuple")
        if any(not isinstance(item, str) for item in self.argv):
            raise ValueError("argv must contain only strings")
        if not isinstance(self.cwd, str) or not self.cwd.strip():
            raise ValueError("cwd must be a non-empty string")
        if self.exit_code is not None and (
            isinstance(self.exit_code, bool) or not isinstance(self.exit_code, int)
        ):
            raise ValueError("exit_code must be an integer when present")
        if not isinstance(self.stdout, str) or not isinstance(self.stderr, str):
            raise ValueError("stdout and stderr must be strings")
        if not isinstance(self.timed_out, bool):
            raise ValueError("timed_out must be boolean")
        if (
            isinstance(self.duration_ms, bool)
            or not isinstance(self.duration_ms, int)
            or self.duration_ms < 0
        ):
            raise ValueError("duration_ms must be a non-negative integer")
        if self.environment_error is not None and not isinstance(
            self.environment_error, CommandEnvironmentError
        ):
            raise ValueError("environment_error must be a CommandEnvironmentError")
        if isinstance(self.schema_version, bool) or self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported command result schema: {self.schema_version}")

    @property
    def process_started(self) -> bool:
        return self.environment_error is None or self.environment_error.kind is EnvironmentErrorKind.TERMINATION_ERROR

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "argv": list(self.argv),
            "cwd": self.cwd,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "timed_out": self.timed_out,
            "duration_ms": self.duration_ms,
            "environment_error": (
                None if self.environment_error is None else self.environment_error.to_dict()
            ),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "CommandResult":
        if not isinstance(value, Mapping):
            raise ValueError("command result must be a mapping")
        schema_version = value.get("schema_version", 0)
        if isinstance(schema_version, bool) or not isinstance(schema_version, int):
            raise ValueError("schema_version must be an integer")
        argv = value.get("argv")
        cwd = value.get("cwd")
        exit_code = value.get("exit_code")
        stdout = value.get("stdout")
        stderr = value.get("stderr")
        timed_out = value.get("timed_out")
        duration_ms = value.get("duration_ms")
        raw_error = value.get("environment_error")
        if not isinstance(argv, list):
            raise ValueError("argv must be a list")
        if not isinstance(cwd, str):
            raise ValueError("cwd must be a string")
        if exit_code is not None and (
            isinstance(exit_code, bool) or not isinstance(exit_code, int)
        ):
            raise ValueError("exit_code must be an integer when present")
        if not isinstance(stdout, str) or not isinstance(stderr, str):
            raise ValueError("stdout and stderr must be strings")
        if not isinstance(timed_out, bool):
            raise ValueError("timed_out must be boolean")
        if isinstance(duration_ms, bool) or not isinstance(duration_ms, int):
            raise ValueError("duration_ms must be an integer")
        if raw_error is not None and not isinstance(raw_error, Mapping):
            raise ValueError("environment_error must be a mapping when present")
        return cls(
            argv=tuple(argv),
            cwd=cwd,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            timed_out=timed_out,
            duration_ms=duration_ms,
            environment_error=(
                None
                if raw_error is None
                else CommandEnvironmentError.from_dict(raw_error)
            ),
            schema_version=schema_version,
        )

    @classmethod
    def from_json(cls, value: str) -> "CommandResult":
        return cls.from_dict(json.loads(value))


class CommandEnvironment(Protocol):
    def execute(self, spec: CommandSpec) -> CommandResult:
        """Execute one command observation without inferring task outcome."""


class LocalCommandEnvironment:
    """Execute one argv vector directly on the local host with bounded time."""

    def execute(self, spec: CommandSpec) -> CommandResult:
        started = time.monotonic_ns()
        cwd = Path(spec.cwd).expanduser().resolve()

        if not cwd.is_dir():
            return _environment_failure(
                spec,
                cwd,
                started,
                EnvironmentErrorKind.CWD_UNAVAILABLE,
                f"working directory is unavailable: {cwd}",
            )

        kwargs: dict[str, Any] = {
            "cwd": str(cwd),
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "shell": False,
        }
        if os.name == "posix":
            kwargs["start_new_session"] = True
        elif os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        try:
            process = subprocess.Popen(list(spec.argv), **kwargs)
        except FileNotFoundError as exc:
            return _environment_failure(
                spec,
                cwd,
                started,
                EnvironmentErrorKind.EXECUTABLE_NOT_FOUND,
                str(exc),
            )
        except PermissionError as exc:
            return _environment_failure(
                spec,
                cwd,
                started,
                EnvironmentErrorKind.PERMISSION_DENIED,
                str(exc),
            )
        except OSError as exc:
            return _environment_failure(
                spec,
                cwd,
                started,
                EnvironmentErrorKind.OS_ERROR,
                str(exc),
            )

        try:
            stdout, stderr = process.communicate(timeout=float(spec.timeout_seconds))
            return CommandResult(
                argv=spec.argv,
                cwd=str(cwd),
                exit_code=process.returncode,
                stdout=stdout,
                stderr=stderr,
                timed_out=False,
                duration_ms=_elapsed_ms(started),
            )
        except subprocess.TimeoutExpired:
            termination_error = _terminate_process_tree(process)
            stdout, stderr = process.communicate()
            return CommandResult(
                argv=spec.argv,
                cwd=str(cwd),
                exit_code=process.returncode,
                stdout=stdout,
                stderr=stderr,
                timed_out=True,
                duration_ms=_elapsed_ms(started),
                environment_error=termination_error,
            )


def _elapsed_ms(started: int) -> int:
    return max(0, (time.monotonic_ns() - started) // 1_000_000)


def _environment_failure(
    spec: CommandSpec,
    cwd: Path,
    started: int,
    kind: EnvironmentErrorKind,
    message: str,
) -> CommandResult:
    return CommandResult(
        argv=spec.argv,
        cwd=str(cwd),
        exit_code=None,
        stdout="",
        stderr="",
        timed_out=False,
        duration_ms=_elapsed_ms(started),
        environment_error=CommandEnvironmentError(kind=kind, message=message),
    )


def _terminate_process_tree(
    process: subprocess.Popen[str],
) -> CommandEnvironmentError | None:
    if process.poll() is not None:
        return None

    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        elif os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                text=True,
                capture_output=True,
                check=False,
                timeout=5,
            )
            if process.poll() is None:
                process.kill()
        else:
            process.kill()
        return None
    except (OSError, subprocess.SubprocessError) as exc:
        try:
            process.kill()
        except OSError:
            pass
        return CommandEnvironmentError(
            kind=EnvironmentErrorKind.TERMINATION_ERROR,
            message=str(exc),
        )
