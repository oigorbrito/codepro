"""Read-only local project inspection for the CodePro CLI."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import subprocess
from typing import Callable


_LANGUAGE_MARKERS = (
    ("Python", ("pyproject.toml", "setup.py", "setup.cfg", "requirements.txt")),
    ("TypeScript", ("tsconfig.json",)),
    ("JavaScript", ("package.json",)),
    ("Go", ("go.mod",)),
    ("Rust", ("Cargo.toml",)),
    ("Java", ("pom.xml", "build.gradle", "build.gradle.kts")),
)

_EXECUTORS = (
    ("Codex", "codex"),
    ("Claude Code", "claude"),
    ("Gemini CLI", "gemini"),
)


@dataclass(frozen=True)
class ProjectInspection:
    project_name: str
    project_root: str
    git_available: bool
    git_repository: bool
    branch: str | None
    languages: tuple[str, ...]
    test_surfaces: tuple[str, ...]
    executors: tuple[tuple[str, str, bool], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "project_name": self.project_name,
            "project_root": self.project_root,
            "git_available": self.git_available,
            "git_repository": self.git_repository,
            "branch": self.branch,
            "languages": list(self.languages),
            "test_surfaces": list(self.test_surfaces),
            "executors": [
                {"name": name, "command": command, "available": available}
                for name, command, available in self.executors
            ],
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )


def _git(
    cwd: Path,
    *args: str,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str | None:
    result = runner(
        ["git", "-C", str(cwd), *args],
        text=True,
        capture_output=True,
        check=False,
        timeout=5,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def inspect_project(
    path: str | Path = ".",
    *,
    which: Callable[[str], str | None] = shutil.which,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> ProjectInspection:
    requested = Path(path).expanduser().resolve()
    if not requested.is_dir():
        raise ValueError(f"project path is not a directory: {requested}")

    git_available = which("git") is not None
    git_root_value = _git(requested, "rev-parse", "--show-toplevel", runner=runner) if git_available else None
    git_repository = git_root_value is not None
    root = Path(git_root_value).resolve() if git_root_value else requested

    branch = None
    if git_repository:
        branch = _git(root, "branch", "--show-current", runner=runner)
        if branch is None:
            detached = _git(root, "rev-parse", "--short", "HEAD", runner=runner)
            branch = f"DETACHED@{detached}" if detached else "DETACHED"

    languages = tuple(
        language
        for language, markers in _LANGUAGE_MARKERS
        if any((root / marker).is_file() for marker in markers)
    )

    test_surfaces = tuple(
        name
        for name in ("tests", "test", "spec")
        if (root / name).is_dir()
    )

    executors = tuple(
        (name, command, which(command) is not None)
        for name, command in _EXECUTORS
    )

    return ProjectInspection(
        project_name=root.name,
        project_root=str(root),
        git_available=git_available,
        git_repository=git_repository,
        branch=branch,
        languages=languages,
        test_surfaces=test_surfaces,
        executors=executors,
    )
