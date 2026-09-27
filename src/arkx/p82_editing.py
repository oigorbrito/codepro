"""B1 structured-editing contract.

This module represents an edit proposal only. It never writes files, applies a
patch, runs validation, selects a target, retries, or changes acceptance.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Any


SCHEMA_VERSION = 1
TREATMENT = "B1"


class EditOperation(str, Enum):
    REPLACE_RANGE = "REPLACE_RANGE"
    APPLY_PATCH = "APPLY_PATCH"


@dataclass(frozen=True)
class StructuredEditProposal:
    """A syntactically bounded edit proposal with no execution semantics."""

    task_id: str
    target_file: str
    operation: EditOperation | str
    replacement_content: str | None = None
    patch_content: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    treatment: str = TREATMENT
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("task_id", "target_file"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must be non-empty")
        if self.treatment != TREATMENT:
            raise ValueError(f"edit proposal treatment must be {TREATMENT}")
        try:
            operation = EditOperation(self.operation)
        except ValueError as error:
            raise ValueError("unsupported structured edit operation") from error
        object.__setattr__(self, "operation", operation)

        has_replacement = self.replacement_content is not None
        has_patch = self.patch_content is not None
        if has_replacement == has_patch:
            raise ValueError("exactly one edit representation must be provided")
        if operation is EditOperation.REPLACE_RANGE:
            if not has_replacement or self.start_line is None or self.end_line is None:
                raise ValueError("REPLACE_RANGE requires replacement content and line range")
            if self.start_line < 1 or self.end_line < self.start_line:
                raise ValueError("edit line range is invalid")
        elif operation is EditOperation.APPLY_PATCH:
            if not has_patch:
                raise ValueError("APPLY_PATCH requires patch content")
            if self.start_line is not None or self.end_line is not None:
                raise ValueError("APPLY_PATCH cannot include a line range")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "treatment": self.treatment,
            "task_id": self.task_id,
            "target_file": self.target_file,
            "operation": self.operation.value,
            "replacement_content": self.replacement_content,
            "patch_content": self.patch_content,
            "start_line": self.start_line,
            "end_line": self.end_line,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def record_edit_proposal(
    *,
    task_id: str,
    target_file: str,
    operation: EditOperation | str,
    replacement_content: str | None = None,
    patch_content: str | None = None,
    start_line: int | None = None,
    end_line: int | None = None,
) -> StructuredEditProposal:
    """Validate and record B1 without applying or evaluating the proposal."""

    return StructuredEditProposal(
        task_id=task_id,
        target_file=target_file,
        operation=operation,
        replacement_content=replacement_content,
        patch_content=patch_content,
        start_line=start_line,
        end_line=end_line,
    )
