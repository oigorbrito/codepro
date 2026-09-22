"""Versioned, serializable contracts for P0 execution telemetry."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = 1


class ExecutionStatus(str, Enum):
    PASS = "PASS"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"
    NOT_EXECUTED = "NOT_EXECUTED"
    UNVERIFIED = "UNVERIFIED"


class EventType(str, Enum):
    TASK_STARTED = "TASK_STARTED"
    EXECUTOR_STARTED = "EXECUTOR_STARTED"
    EXECUTOR_FINISHED = "EXECUTOR_FINISHED"
    RETRY = "RETRY"
    REPLAN = "REPLAN"
    HANDOFF = "HANDOFF"
    EVIDENCE_ADDED = "EVIDENCE_ADDED"
    HUMAN_INTERVENTION = "HUMAN_INTERVENTION"
    TASK_FINISHED = "TASK_FINISHED"


@dataclass(frozen=True)
class Event:
    timestamp: str
    type: EventType
    run_id: str
    data: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "type": self.type.value,
            "run_id": self.run_id,
            "data": dict(self.data),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Event":
        return cls(
            timestamp=str(value["timestamp"]),
            type=EventType(value["type"]),
            run_id=str(value["run_id"]),
            data=dict(value.get("data", {})),
        )


@dataclass
class ExecutionRecord:
    task_id: str
    run_id: str
    executor_id: str | None
    started_at: str | None
    finished_at: str | None
    status: ExecutionStatus
    decision_reason: str | None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    monetary_cost: float | None = None
    wall_time_ms: int | None = None
    retry_count: int = 0
    replan_count: int = 0
    executor_invocations: int = 0
    handoff_count: int = 0
    human_interventions: int = 0
    evidence_refs: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": self.schema_version,
            "task_id": self.task_id,
            "run_id": self.run_id,
            "executor_id": self.executor_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "status": self.status.value,
            "decision_reason": self.decision_reason,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "monetary_cost": self.monetary_cost,
            "wall_time_ms": self.wall_time_ms,
            "retry_count": self.retry_count,
            "replan_count": self.replan_count,
            "executor_invocations": self.executor_invocations,
            "handoff_count": self.handoff_count,
            "human_interventions": self.human_interventions,
            "evidence_refs": list(self.evidence_refs),
            "errors": list(self.errors),
            "metadata": dict(self.metadata),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def write_json(self, path: str | Path) -> None:
        """Write one deterministic record; callers choose the experiment path."""

        Path(path).write_text(self.to_json() + "\n", encoding="utf-8")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ExecutionRecord":
        schema_version = int(value.get("schemaVersion", 0))
        if schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported execution record schema: {schema_version}")
        return cls(
            task_id=str(value["task_id"]),
            run_id=str(value["run_id"]),
            executor_id=value.get("executor_id"),
            started_at=value.get("started_at"),
            finished_at=value.get("finished_at"),
            status=ExecutionStatus(value["status"]),
            decision_reason=value.get("decision_reason"),
            input_tokens=value.get("input_tokens"),
            output_tokens=value.get("output_tokens"),
            total_tokens=value.get("total_tokens"),
            monetary_cost=value.get("monetary_cost"),
            wall_time_ms=value.get("wall_time_ms"),
            retry_count=int(value.get("retry_count", 0)),
            replan_count=int(value.get("replan_count", 0)),
            executor_invocations=int(value.get("executor_invocations", 0)),
            handoff_count=int(value.get("handoff_count", 0)),
            human_interventions=int(value.get("human_interventions", 0)),
            evidence_refs=list(value.get("evidence_refs", [])),
            errors=list(value.get("errors", [])),
            metadata=dict(value.get("metadata", {})),
            schema_version=schema_version,
        )

    @classmethod
    def from_json(cls, value: str) -> "ExecutionRecord":
        return cls.from_dict(json.loads(value))
