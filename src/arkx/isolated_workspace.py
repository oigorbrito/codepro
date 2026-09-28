"""Isolated Git worktree boundary for reproducible task execution."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any


@dataclass(frozen=True)
class GitCommandObservation:
    argv: tuple[str, ...]
    returncode: int | None
    stdout: str
    stderr: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "argv": list(self.argv),
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


@dataclass(frozen=True)
class RepositoryState:
    revision: str
    status_porcelain: str
    clean: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "revision": self.revision,
            "status_porcelain": self.status_porcelain,
            "clean": self.clean,
        }


@dataclass(frozen=True)
class WorkspaceCleanup:
    removed: bool
    remove: GitCommandObservation
    prune: GitCommandObservation

    def to_dict(self) -> dict[str, Any]:
        return {
            "removed": self.removed,
            "remove": self.remove.to_dict(),
            "prune": self.prune.to_dict(),
        }


class IsolatedGitWorkspace:
    """Own one detached worktree created from an exact source revision."""

    def __init__(
        self,
        *,
        source_repository: Path,
        workspace: Path,
        revision: str,
        creation: GitCommandObservation,
        initial_state: RepositoryState,
    ) -> None:
        self.source_repository = source_repository
        self.workspace = workspace
        self.revision = revision
        self.creation = creation
        self.initial_state = initial_state
        self._removed = False

    @classmethod
    def create(
        cls,
        *,
        source_repository: str | Path,
        revision: str,
        workspace_root: str | Path,
        workspace_id: str,
    ) -> "IsolatedGitWorkspace":
        source = Path(source_repository).expanduser().resolve()
        root = Path(workspace_root).expanduser().resolve()
        if not source.is_dir():
            raise ValueError("source_repository must be an existing directory")
        if not revision.strip():
            raise ValueError("revision must be non-empty")
        if not workspace_id.strip() or Path(workspace_id).name != workspace_id:
            raise ValueError("workspace_id must be a single non-empty path component")
        if root == source or source in root.parents:
            raise ValueError("workspace_root must be outside the source repository")

        root.mkdir(parents=True, exist_ok=True)
        workspace = (root / workspace_id).resolve()
        if root not in workspace.parents:
            raise ValueError("workspace path escapes workspace_root")
        if workspace.exists():
            raise FileExistsError(f"isolated workspace already exists: {workspace}")

        resolved = _git(source, "rev-parse", "--verify", f"{revision}^{{commit}}")
        if resolved.returncode != 0:
            raise ValueError(f"revision is unavailable: {revision}")
        exact_revision = resolved.stdout.strip()
        if not exact_revision:
            raise ValueError("resolved revision is empty")

        creation = _git(
            source,
            "worktree",
            "add",
            "--detach",
            str(workspace),
            exact_revision,
        )
        if creation.returncode != 0:
            raise RuntimeError(
                "unable to create isolated worktree: "
                + (creation.stderr.strip() or "unknown git worktree error")
            )

        try:
            initial_state = capture_repository_state(workspace)
            if initial_state.revision != exact_revision:
                raise RuntimeError("isolated worktree revision does not match requested revision")
            if not initial_state.clean:
                raise RuntimeError("isolated worktree must start clean")
        except Exception:
            _git(source, "worktree", "remove", "--force", str(workspace))
            _git(source, "worktree", "prune")
            raise

        return cls(
            source_repository=source,
            workspace=workspace,
            revision=exact_revision,
            creation=creation,
            initial_state=initial_state,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_repository": str(self.source_repository),
            "workspace": str(self.workspace),
            "revision": self.revision,
            "creation": self.creation.to_dict(),
            "initial_state": self.initial_state.to_dict(),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def capture_state(self) -> RepositoryState:
        if self._removed:
            raise RuntimeError("isolated workspace has already been removed")
        return capture_repository_state(self.workspace)

    def remove(self) -> WorkspaceCleanup:
        if self._removed:
            raise RuntimeError("isolated workspace has already been removed")
        remove = _git(
            self.source_repository,
            "worktree",
            "remove",
            "--force",
            str(self.workspace),
        )
        prune = _git(self.source_repository, "worktree", "prune")
        removed = remove.returncode == 0 and not self.workspace.exists()
        self._removed = removed
        return WorkspaceCleanup(removed, remove, prune)


def capture_repository_state(workspace: str | Path) -> RepositoryState:
    root = Path(workspace).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("workspace must be an existing directory")

    head = _git(root, "rev-parse", "HEAD")
    if head.returncode != 0:
        raise RuntimeError("unable to record repository revision")

    status = _git(root, "status", "--porcelain=v1", "--untracked-files=all")
    if status.returncode != 0:
        raise RuntimeError("unable to record repository status")

    return RepositoryState(
        revision=head.stdout.strip(),
        status_porcelain=status.stdout,
        clean=not bool(status.stdout.strip()),
    )


def _git(root: Path, *args: str) -> GitCommandObservation:
    argv = ("git", "-C", str(root), *args)
    try:
        completed = subprocess.run(
            list(argv),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            check=False,
            timeout=30,
        )
        return GitCommandObservation(
            tuple(argv),
            completed.returncode,
            completed.stdout,
            completed.stderr,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return GitCommandObservation(tuple(argv), None, "", str(exc))
