"""Explicit handoff and context accounting records for P6."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Any


SCHEMA_VERSION = 2


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class HandoffBudgetStatus(_ValueEnum):
    WITHIN_BUDGET = "WITHIN_BUDGET"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    UNKNOWN = "UNKNOWN"


def _values(items: tuple[str, ...] | None) -> list[str] | None:
    return None if items is None else sorted(set(items))


@dataclass(frozen=True)
class HandoffRecord:
    handoff_id: str
    source_executor: str | None
    target_executor: str | None
    reason: str | None
    evidence_refs: tuple[str, ...] | None
    context_summary: str | None
    context_bytes_in: int | None
    context_bytes_out: int | None
    duplicated_instructions: int | None
    duplicated_exploration: int | None
    discarded_context: int | None
    lost_information: tuple[str, ...] | None
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.handoff_id.strip():
            raise ValueError("handoff_id must be non-empty")
        for name in ("source_executor", "target_executor", "reason", "context_summary"):
            value = getattr(self, name)
            if value is not None and not value.strip():
                raise ValueError(f"{name} cannot be blank")
        if self.evidence_refs is not None and any(not item.strip() for item in self.evidence_refs):
            raise ValueError("evidence_refs cannot contain blank references")
        for name in (
            "context_bytes_in",
            "context_bytes_out",
            "duplicated_instructions",
            "duplicated_exploration",
            "discarded_context",
        ):
            value = getattr(self, name)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value < 0
            ):
                raise ValueError(f"{name} must be a non-negative integer when present")
        if self.lost_information is not None and any(
            not item.strip() for item in self.lost_information
        ):
            raise ValueError("lost_information cannot contain blank declarations")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "handoff_id": self.handoff_id,
            "source_executor": self.source_executor,
            "target_executor": self.target_executor,
            "reason": self.reason,
            "evidence_refs": _values(self.evidence_refs),
            "context_summary": self.context_summary,
            "context_bytes_in": self.context_bytes_in,
            "context_bytes_out": self.context_bytes_out,
            "duplicated_instructions": self.duplicated_instructions,
            "duplicated_exploration": self.duplicated_exploration,
            "discarded_context": self.discarded_context,
            "lost_information": _values(self.lost_information),
        }


@dataclass(frozen=True)
class HandoffPolicy:
    max_handoffs: int = 2
    max_executor_transitions: int = 2

    def __post_init__(self) -> None:
        for name in ("max_handoffs", "max_executor_transitions"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")


@dataclass(frozen=True)
class HandoffSummary:
    handoffs: int
    executor_transitions: tuple[tuple[str, str], ...]
    context_bytes_in: int | None
    context_bytes_out: int | None
    duplicated_instructions: int | None
    duplicated_exploration: int | None
    discarded_context: int | None
    lost_information_count: int | None
    budget_status: HandoffBudgetStatus
    schema_version: int = SCHEMA_VERSION
    telemetry: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "handoffs": self.handoffs,
            "executor_transitions": [list(edge) for edge in self.executor_transitions],
            "context_bytes_in": self.context_bytes_in,
            "context_bytes_out": self.context_bytes_out,
            "duplicated_instructions": self.duplicated_instructions,
            "duplicated_exploration": self.duplicated_exploration,
            "discarded_context": self.discarded_context,
            "lost_information_count": self.lost_information_count,
            "budget_status": self.budget_status.value,
            "telemetry": self.telemetry,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def summarize_handoffs(
    records: tuple[HandoffRecord, ...],
    policy: HandoffPolicy | None = None,
) -> HandoffSummary:
    policy = policy or HandoffPolicy()
    ids = [record.handoff_id for record in records]
    if len(set(ids)) != len(ids):
        raise ValueError("handoff_id values must be unique within one summary")

    transitions = tuple(
        (record.source_executor, record.target_executor)
        for record in records
        if record.source_executor is not None and record.target_executor is not None
    )

    def total(field: str) -> int | None:
        values = [getattr(record, field) for record in records]
        return None if any(value is None for value in values) else sum(values)

    lost_values = [record.lost_information for record in records]
    lost_count = (
        None
        if any(value is None for value in lost_values)
        else sum(len(value) for value in lost_values)
    )

    if len(records) > policy.max_handoffs or len(transitions) > policy.max_executor_transitions:
        budget_status = HandoffBudgetStatus.BUDGET_EXCEEDED
    elif any(
        record.source_executor is None or record.target_executor is None for record in records
    ):
        budget_status = HandoffBudgetStatus.UNKNOWN
    else:
        budget_status = HandoffBudgetStatus.WITHIN_BUDGET

    return HandoffSummary(
        handoffs=len(records),
        executor_transitions=transitions,
        context_bytes_in=total("context_bytes_in"),
        context_bytes_out=total("context_bytes_out"),
        duplicated_instructions=total("duplicated_instructions"),
        duplicated_exploration=total("duplicated_exploration"),
        discarded_context=total("discarded_context"),
        lost_information_count=lost_count,
        budget_status=budget_status,
        telemetry={
            "handoffs": len(records),
            "executor_transitions": len(transitions),
            "context_bytes_in": total("context_bytes_in"),
            "context_bytes_out": total("context_bytes_out"),
            "duplicated_instructions": total("duplicated_instructions"),
            "duplicated_exploration": total("duplicated_exploration"),
            "discarded_context": total("discarded_context"),
            "lost_information_count": lost_count,
        },
    )
