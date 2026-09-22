"""Small deterministic event collector for executor-agnostic P0 metrics."""

from __future__ import annotations

from datetime import datetime
from numbers import Real
from typing import Any

from .contracts import Event, EventType, ExecutionRecord, ExecutionStatus
from .evidence import resolve_status


def _timestamp(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid event timestamp: {value!r}") from exc


def _sum_optional(events: list[Event], key: str, *, numeric_type: type) -> int | float | None:
    values: list[int | float] = []
    for event in events:
        value = event.data.get(key)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, numeric_type):
            raise ValueError(f"Event field {key!r} must be numeric when present")
        values.append(value)
    return sum(values) if values else None


class TelemetryCollector:
    """Collect events without making execution or policy decisions."""

    def __init__(self, *, task_id: str, run_id: str):
        self.task_id = task_id
        self.run_id = run_id
        self._events: list[Event] = []

    def add(self, event: Event) -> None:
        if event.run_id != self.run_id:
            raise ValueError(f"Event run_id {event.run_id!r} does not match {self.run_id!r}")
        _timestamp(event.timestamp)
        self._events.append(event)

    def extend(self, events: list[Event]) -> None:
        for event in events:
            self.add(event)

    @property
    def events(self) -> tuple[Event, ...]:
        return tuple(self._events)

    def summarize(self) -> ExecutionRecord:
        events = list(self._events)
        task_starts = [event for event in events if event.type is EventType.TASK_STARTED]
        task_finishes = [event for event in events if event.type is EventType.TASK_FINISHED]
        evidence_refs: list[str] = []
        errors: list[str] = []
        executor_id: str | None = None

        for event in events:
            if event.type is EventType.EXECUTOR_STARTED and executor_id is None:
                value = event.data.get("executor_id")
                executor_id = str(value) if value is not None else None
            if event.type is EventType.EVIDENCE_ADDED:
                ref = event.data.get("ref")
                refs = event.data.get("refs", [])
                if ref is not None:
                    evidence_refs.append(str(ref))
                if not isinstance(refs, list):
                    raise ValueError("EVIDENCE_ADDED refs must be a list when present")
                evidence_refs.extend(str(value) for value in refs)
            if event.data.get("error") is not None:
                errors.append(str(event.data["error"]))

        started_at = task_starts[0].timestamp if task_starts else None
        finished_at = task_finishes[-1].timestamp if task_finishes else None
        wall_time_ms: int | None = None
        if started_at is not None and finished_at is not None:
            wall_time_ms = int((_timestamp(finished_at) - _timestamp(started_at)).total_seconds() * 1000)

        requested = None
        reason = None
        if task_finishes:
            requested = task_finishes[-1].data.get("status")
            reason_value = task_finishes[-1].data.get("decision_reason")
            reason = str(reason_value) if reason_value is not None else None
        status = resolve_status(requested, evidence_refs) if task_finishes else ExecutionStatus.NOT_EXECUTED

        handoff_metadata = [
            {
                "source_executor": event.data.get("source_executor"),
                "target_executor": event.data.get("target_executor"),
                "reason": event.data.get("reason"),
            }
            for event in events
            if event.type is EventType.HANDOFF
        ]
        metadata: dict[str, Any] = {"handoffs": handoff_metadata}

        return ExecutionRecord(
            task_id=self.task_id,
            run_id=self.run_id,
            executor_id=executor_id,
            started_at=started_at,
            finished_at=finished_at,
            status=status,
            decision_reason=reason,
            input_tokens=_sum_optional(events, "input_tokens", numeric_type=int),
            output_tokens=_sum_optional(events, "output_tokens", numeric_type=int),
            total_tokens=_sum_optional(events, "total_tokens", numeric_type=int),
            monetary_cost=_sum_optional(events, "monetary_cost", numeric_type=Real),
            wall_time_ms=wall_time_ms,
            retry_count=sum(event.type is EventType.RETRY for event in events),
            replan_count=sum(event.type is EventType.REPLAN for event in events),
            executor_invocations=sum(event.type is EventType.EXECUTOR_STARTED for event in events),
            handoff_count=sum(event.type is EventType.HANDOFF for event in events),
            human_interventions=sum(event.type is EventType.HUMAN_INTERVENTION for event in events),
            evidence_refs=evidence_refs,
            errors=errors,
            metadata=metadata,
        )

