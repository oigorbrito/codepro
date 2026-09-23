"""Versioned, serializable contracts for P0 execution telemetry."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from math import isfinite
import json
from pathlib import Path
from typing import Any, Mapping


def _nonblank_string(name: str, value: Any, *, optional: bool = false):
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-blank string")
    return value


def _nonnegative_int(name: str, value: Any, *, optional: bool = false):
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _optional_timestamp(name: str, value: Any):
    if value is None:
        return None
    text = _nonblank_string(name, value)
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO-8601 timestamp") from exc
    return text


def _strict_json(value: Any) -> None:
    try:
        json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("record contains non-finite or non-JSON data") from exc


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

    def __post_init__(self) -> None:
        _optional_timestamp("timestamp", self.timestamp)
        _nonblank_string("run_id", self.run_id)
        if not isinstance(self.type, EventType):
            raise ValueError("type must be an EventType")
        if not isinstance(self.data, Mapping):
            raise ValueError("data must be a mapping")
        _strict_json(dict(self.data))

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "type": self.type.value,
            "run_id": self.run_id,
            "data": dict(self.data),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Event":
        if not isinstance(value, Mapping):
            raise ValueError("event payload must be a mapping")
        timestamp = _nonblank_string("timestamp", value.get("timestamp"))
        run_id = _nonblank_string("run_id", value.get("run_id"))
        raw_type = value.get("type")
        if not isinstance(raw_type, str):
            raise ValueError("type must be a string enum value")
        raw_data = value.get("data", {})
        if not isinstance(raw_data, Mapping):
            raise ValueError("data must be a mapping")
        return cls(
            timestamp=timestamp,
            type=EventType(raw_type),
            run_id=run_id,
            data=dict(raw_data),
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

    def __post_init__(self) -> None:
        _nonblank_string("task_id", self.task_id)
        _nonblank_string("run_id", self.run_id)
        if self.executor_id is not None:
            _nonblank_string("executor_id", self.executor_id)
        started = _optional_timestamp("started_at", self.started_at)
        finished = _optional_timestamp("finished_at", self.finished_at)
        if started is not None and finished is not None:
            start_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
            finish_dt = datetime.fromisoformat(finished.replace("Z", "+00:00"))
            if finish_dt < start_dt:
                raise ValueError("finished_at cannot precede started_at")
        if not isinstance(self.status, ExecutionStatus):
            raise ValueError("status must be an ExecutionStatus")
        if self.decision_reason is not None:
            _nonblank_string("decision_reason", self.decision_reason)
        for name in ("input_tokens", "output_tokens", "total_tokens", "wall_time_ms"):
            _nonnegative_int(name, getattr(self, name), optional=True)
        for name in ("retry_count", "replan_count", "executor_invocations", "handoff_count", "human_interventions"):
            _nonnegative_int(name, getattr(self, name))
        if self.monetary_cost is not None:
            if isinstance(self.monetary_cost, bool) or not isinstance(self.monetary_cost, (int, float)):
                raise ValueError("monetary_cost must be numeric when present")
            if not isfinite(float(self.monetary_cost)) or self.monetary_cost < 0:
                raise ValueError("monetary_cost must be finite and non-negative")
        if not isinstance(self.evidence_refs, list) or any(
            not isinstance(ref, str) or not ref.strip() for ref in self.evidence_refs
        ):
            raise ValueError("evidence_refs must contain only non-blank strings")
        if not isinstance(self.errors, list) or any(not isinstance(item, str) for item in self.errors):
            raise ValueError("errors must be a list of strings")
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dictionary")
        if isinstance(self.schema_version, bool) or self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported execution record schema: {self.schema_version}")
        _strict_json(self.to_dict())

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
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)

    def write_json(self, path: str | Path) -> None:
        """Write one deterministic record; callers choose the experiment path."""

        Path(path).write_text(self.to_json() + "\n", encoding="utf-8")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ExecutionRecord":
        if not isinstance(value, Mapping):
            raise ValueError("execution record payload must be a mapping")
        schema_version = value.get("schemaVersion", 0)
        if isinstance(schema_version, bool) or not isinstance(schema_version, int) or schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported execution record schema: {schema_version}")
        raw_status = value.get("status")
        if not isinstance(raw_status, str):
            raise ValueError("status must be a string enum value")
        refs = value.get("evidence_refs", [])
        errors = value.get("errors", [])
        metadata = value.get("metadata", {})
        if not isinstance(refs, list):
            raise ValueError("evidence_refs must be a list")
        if not isinstance(errors, list):
            raise ValueError("errors must be a list")
        if not isinstance(metadata, Mapping):
            raise ValueError("metadata must be a mapping")
        return cls(
            task_id=_nonblank_string("task_id", value.get("task_id")),
            run_id=_nonblank_string("run_id", value.get("run_id")),
            executor_id=value.get("executor_id"),
            started_at=value.get("started_at"),
            finished_at=value.get("finished_at"),
            status=ExecutionStatus(raw_status),
            decision_reason=value.get("decision_reason"),
            input_tokens=value.get("input_tokens"),
            output_tokens=value.get("output_tokens"),
            total_tokens=value.get("total_tokens"),
            monetary_cost=value.get("monetary_cost"),
            wall_time_ms=value.get("wall_time_ms"),
            retry_count=value.get("retry_count", 0),
            replan_count=value.get("replan_count", 0),
            executor_invocations=value.get("executor_invocations", 0),
            handoff_count=value.get("handoff_count", 0),
            human_interventions=value.get("human_interventions", 0),
            evidence_refs=list(refs),
            errors=list(errors),
            metadata=dict(metadata),
            schema_version=schema_version,
        )

    @classmethod
    def from_json(cls, value: str) -> "ExecutionRecord":
        return cls.from_dict(json.loads(value))
