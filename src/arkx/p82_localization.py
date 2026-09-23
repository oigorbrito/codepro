"""C1 repository-localization contract.

This module specifies the artifact boundary for Treatment C1. It deliberately
does not implement repository search, ranking, prompting, or execution.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any


SCHEMA_VERSION = 1
TREATMENT = "C1"


def _sorted_unique(values: tuple[str, ...]) -> tuple[str, ...]:
    if any(not value or not value.strip() for value in values):
        raise ValueError("localization values must be non-empty")
    return tuple(sorted(set(values)))


@dataclass(frozen=True)
class LocalizationEvidenceBudget:
    """Hard cap for evidence emitted by one localization pass."""

    max_files: int
    max_symbols: int
    max_context_lines: int
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("max_files", "max_symbols", "max_context_lines"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")

    def to_dict(self) -> dict[str, int]:
        return {
            "max_files": self.max_files,
            "max_symbols": self.max_symbols,
            "max_context_lines": self.max_context_lines,
        }


@dataclass(frozen=True)
class LocalizationArtifact:
    """Bounded, non-authoritative output of a future C1 localization pass."""

    task_id: str
    repository_revision: str
    localization_method: str
    candidate_files: tuple[str, ...]
    candidate_symbols: tuple[str, ...]
    context_lines_used: int
    evidence_budget: LocalizationEvidenceBudget
    candidates_are_non_authoritative: bool = True
    treatment: str = TREATMENT
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("task_id", "repository_revision", "localization_method"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if self.treatment != TREATMENT:
            raise ValueError(f"localization artifact treatment must be {TREATMENT}")
        if not self.candidates_are_non_authoritative:
            raise ValueError("C1 candidates must be explicitly non-authoritative")
        if self.context_lines_used < 0:
            raise ValueError("context_lines_used must be non-negative")

        files = _sorted_unique(self.candidate_files)
        symbols = _sorted_unique(self.candidate_symbols)
        if len(files) > self.evidence_budget.max_files:
            raise ValueError("candidate file count exceeds evidence budget")
        if len(symbols) > self.evidence_budget.max_symbols:
            raise ValueError("candidate symbol count exceeds evidence budget")
        if self.context_lines_used > self.evidence_budget.max_context_lines:
            raise ValueError("context line count exceeds evidence budget")
        object.__setattr__(self, "candidate_files", files)
        object.__setattr__(self, "candidate_symbols", symbols)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "treatment": self.treatment,
            "task_id": self.task_id,
            "repository_revision": self.repository_revision,
            "localization_method": self.localization_method,
            "candidate_files": list(self.candidate_files),
            "candidate_symbols": list(self.candidate_symbols),
            "context_lines_used": self.context_lines_used,
            "evidence_budget": self.evidence_budget.to_dict(),
            "candidates_are_non_authoritative": self.candidates_are_non_authoritative,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def record_localization_artifact(
    *,
    task_id: str,
    repository_revision: str,
    localization_method: str,
    candidate_files: tuple[str, ...] = (),
    candidate_symbols: tuple[str, ...] = (),
    context_lines_used: int = 0,
    evidence_budget: LocalizationEvidenceBudget,
) -> LocalizationArtifact:
    """Validate and record C1 output without performing localization."""

    return LocalizationArtifact(
        task_id=task_id,
        repository_revision=repository_revision,
        localization_method=localization_method,
        candidate_files=candidate_files,
        candidate_symbols=candidate_symbols,
        context_lines_used=context_lines_used,
        evidence_budget=evidence_budget,
    )
