"""Repository operation primitives for scaffold adapters.

This module provides explicit inspect/edit/command mechanics inside one
pre-existing task workspace. It does not select a scaffold, model, executor,
verifier, or acceptance decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
from pathlib import Path
import time
from typing import Any, Sequence

from .command import CommandSpec, LocalCommandEnvironment
from .p82_localization import canonicalize_repository_relative_path


class RepositoryOperationKind(str, Enum):
    INSPECT = "INSPECT"
    EDIT = "EDIT"
    COMMAND = "COMMAND"


@dataclass(frozen=True)
class RepositoryOperationObservation:
    kind: RepositoryOperationKind
    target_file: str | None
    argv: tuple[str, ...]
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool
    duration_ms: int
    content_sha256: str | None = None
    bytes_observed: int | None = None
    environment_error: dict[str, str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "target_file": self.target_file,
            "argv": list(self.argv),
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "timed_out": self.timed_out,
            "duration_ms": self.duration_ms,
            "content_sha256": self.content_sha256,
            "bytes_observed": self.bytes_observed,
            "environment_error": self.environment_error,
        }


class RepositoryToolbox:
    """Explicit repository-local operations for one already-authorized workspace."""

    def __init__(
        self,
        workspace: str | Path,
        *,
        authorized_scope: Sequence[str],
    ) -> None:
        self.workspace = Path(workspace).expanduser().resolve()
        if not self.workspace.is_dir():
            raise ValueError("workspace must be an existing directory")
        scopes = tuple(
            sorted(
                {
                    canonicalize_repository_relative_path(item)
                    for item in authorized_scope
                    if item.strip()
                }
            )
        )
        if not scopes:
            raise ValueError("authorized_scope must be non-empty")
        self.authorized_scope = scopes
        self.environment = LocalCommandEnvironment()

    def inspect(self, path: str) -> RepositoryOperationObservation:
        relative, target = self._authorized_target(path)
        if not target.is_file():
            raise ValueError(f"inspect target must be an existing file: {relative}")

        started = time.monotonic()
        content = target.read_text(encoding="utf-8")
        duration_ms = int((time.monotonic() - started) * 1000)
        raw = content.encode("utf-8")
        return RepositoryOperationObservation(
            kind=RepositoryOperationKind.INSPECT,
            target_file=relative,
            argv=(),
            exit_code=0,
            stdout=content,
            stderr="",
            timed_out=False,
            duration_ms=duration_ms,
            content_sha256=hashlib.sha256(raw).hexdigest(),
            bytes_observed=len(raw),
        )

    def edit(self, path: str, content: str) -> RepositoryOperationObservation:
        if not isinstance(content, str):
            raise ValueError("edit content must be a string")
        relative, target = self._authorized_target(path)
        if target.exists() and target.is_symlink():
            raise ValueError("edit target must not be a symlink")
        if target.parent != self.workspace and self.workspace not in target.parent.parents:
            raise ValueError("edit target parent escapes workspace")

        started = time.monotonic()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="")
        duration_ms = int((time.monotonic() - started) * 1000)
        raw = content.encode("utf-8")
        return RepositoryOperationObservation(
            kind=RepositoryOperationKind.EDIT,
            target_file=relative,
            argv=(),
            exit_code=0,
            stdout="",
            stderr="",
            timed_out=False,
            duration_ms=duration_ms,
            content_sha256=hashlib.sha256(raw).hexdigest(),
            bytes_observed=len(raw),
        )

    def command(
        self,
        argv: Sequence[str],
        *,
        timeout_seconds: float,
    ) -> RepositoryOperationObservation:
        result = self.environment.execute(
            CommandSpec(
                argv=tuple(argv),
                cwd=str(self.workspace),
                timeout_seconds=timeout_seconds,
            )
        )
        error = (
            None
            if result.environment_error is None
            else result.environment_error.to_dict()
        )
        return RepositoryOperationObservation(
            kind=RepositoryOperationKind.COMMAND,
            target_file=None,
            argv=result.argv,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=result.timed_out,
            duration_ms=result.duration_ms,
            environment_error=error,
        )

    def _authorized_target(self, path: str) -> tuple[str, Path]:
        relative = canonicalize_repository_relative_path(path)
        if not any(
            relative == scope or relative.startswith(scope + "/")
            for scope in self.authorized_scope
        ):
            raise ValueError(f"repository path is outside authorized scope: {relative}")

        target = (self.workspace / relative).resolve(strict=False)
        if target != self.workspace and self.workspace not in target.parents:
            raise ValueError("repository path escapes workspace")
        return relative, target
