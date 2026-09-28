"""Deterministic, no-network P0 baseline fixture."""

from .contracts import Event, EventType
from .telemetry import TelemetryCollector


RUN_ID = "baseline-fixture-run"


def baseline_events() -> list[Event]:
    return [
        Event("2026-01-01T00:00:00+00:00", EventType.TASK_STARTED, RUN_ID, {"task_id": "baseline-task"}),
        Event("2026-01-01T00:00:00.100000+00:00", EventType.EXECUTOR_STARTED, RUN_ID, {"executor_id": "fixture"}),
        Event("2026-01-01T00:00:00.200000+00:00", EventType.EVIDENCE_ADDED, RUN_ID, {"ref": "fixture://evidence/1"}),
        Event("2026-01-01T00:00:00.300000+00:00", EventType.EXECUTOR_FINISHED, RUN_ID, {"total_tokens": 12}),
        Event(
            "2026-01-01T00:00:00.500000+00:00",
            EventType.TASK_FINISHED,
            RUN_ID,
            {"status": "PASS", "decision_reason": "deterministic fixture completed"},
        ),
    ]


def build_baseline_record():
    collector = TelemetryCollector(task_id="baseline-task", run_id=RUN_ID)
    collector.extend(baseline_events())
    return collector.summarize()


def main() -> int:
    print(build_baseline_record().to_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

