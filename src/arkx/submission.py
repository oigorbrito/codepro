"""Explicit submission identity for agent output sent to an evaluator."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import subprocess


UPSTREAM_AGENT = "upstream_agent"
WORKSPACE_DIFF = "workspace_diff"


@dataclass(frozen=True)
class SubmissionArtifact:
    source: str
    raw_submission: str
    normalized_patch: str
    patch_sha256: str
    changed_paths: tuple[str, ...]
    raw_sha256: str
    normalized_sha256: str
    attempt_id: str | None = None
    executor_identity: str | None = None

    @classmethod
    def from_upstream_agent(
        cls,
        submission: str | None,
        *,
        attempt_id: str,
        executor_identity: str,
    ) -> "SubmissionArtifact":
        """Preserve the upstream agent result without falling back to a workspace diff."""
        if submission is None:
            raise ValueError("upstream submission is required; workspace diff fallback is forbidden")
        if not attempt_id or not executor_identity:
            raise ValueError("attempt_id and executor_identity are required")
        raw_sha256 = hashlib.sha256(submission.encode("utf-8")).hexdigest()
        return cls(
            UPSTREAM_AGENT,
            submission,
            submission,
            raw_sha256,
            (),
            raw_sha256,
            raw_sha256,
            attempt_id,
            executor_identity,
        )

    @classmethod
    def from_git_workspace(cls, workspace: str | Path) -> "SubmissionArtifact":
        root = Path(workspace)
        result = subprocess.run(
            ["git", "diff", "--binary"], cwd=root, text=True,
            capture_output=True, check=False,
        )
        if result.returncode and "not a git repository" not in result.stderr.lower():
            raise RuntimeError(result.stderr.strip() or "git diff failed")
        names = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"], cwd=root,
            text=True, capture_output=True, check=False,
        )
        paths: list[str] = []
        for line in names.stdout.splitlines():
            if len(line) > 3:
                path = line[3:]
                if " -> " in path:
                    path = path.split(" -> ", 1)[1]
                paths.append(path)
        raw = result.stdout
        normalized = raw.replace("\r\n", "\n").replace("\r", "\n")
        normalized_sha256 = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return cls(
            WORKSPACE_DIFF,
            raw,
            normalized,
            normalized_sha256,
            tuple(sorted(set(paths))),
            hashlib.sha256(raw.encode("utf-8")).hexdigest(),
            normalized_sha256,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "raw_submission": self.raw_submission,
            "normalized_patch": self.normalized_patch,
            "patch_sha256": self.patch_sha256,
            "changed_paths": list(self.changed_paths),
            "raw_sha256": self.raw_sha256,
            "normalized_sha256": self.normalized_sha256,
            "attempt_id": self.attempt_id,
            "executor_identity": self.executor_identity,
        }
