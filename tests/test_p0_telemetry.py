import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from arkx.baseline import RUN_ID, baseline_events, build_baseline_record
from arkx.contracts import Event, EventType, ExecutionStatus
from arkx.evidence import resolve_status
from arkx.telemetry import TelemetryCollector


def collector(events, *, task_id="task", run_id="run"):
    value = TelemetryCollector(task_id=task_id, run_id=run_id)
    value.extend(events)
    return value


def event(event_type, data=None, *, timestamp="2026-01-01T00:00:00+00:00", run_id="run"):
    return Event(timestamp, event_type, run_id, data or {})


class StatusTests(unittest.TestCase):
    def test_missing_evidence_cannot_become_pass(self):
        self.assertEqual(resolve_status("PASS", []), ExecutionStatus.UNVERIFIED)
        record = collector([event(EventType.TASK_FINISHED, {"status": "PASS"})]).summarize()
        self.assertEqual(record.status, ExecutionStatus.UNVERIFIED)

    def test_blank_evidence_cannot_become_pass(self):
        self.assertEqual(resolve_status("PASS", ["", "   "]), ExecutionStatus.UNVERIFIED)
        with self.assertRaises(ValueError):
            collector([
                event(EventType.EVIDENCE_ADDED, {"ref": "   "}),
                event(EventType.TASK_FINISHED, {"status": "PASS"}),
            ])

    def test_evidence_cannot_be_added_after_finish(self):
        with self.assertRaises(ValueError):
            collector([
                event(EventType.TASK_FINISHED, {"status": "PASS"}),
                event(EventType.EVIDENCE_ADDED, {"ref": "evidence://late"}),
            ])

    def test_duplicate_task_boundaries_are_rejected(self):
        with self.assertRaises(ValueError):
            collector([
                event(EventType.TASK_STARTED),
                event(EventType.TASK_STARTED),
            ])

    def test_regressive_event_timestamps_are_rejected(self):
        with self.assertRaises(ValueError):
            collector([
                event(EventType.TASK_STARTED, timestamp="2026-01-01T00:00:01+00:00"),
                event(EventType.TASK_FINISHED, timestamp="2026-01-01T00:00:00+00:00"),
            ])

    def test_blocked_remains_blocked(self):
        record = collector([event(EventType.TASK_FINISHED, {"status": "BLOCKED"})]).summarize()
        self.assertEqual(record.status, ExecutionStatus.BLOCKED)

    def test_not_executed_is_distinct_from_failed(self):
        not_executed = collector([]).summarize()
        failed = collector([event(EventType.TASK_FINISHED, {"status": "FAILED"})]).summarize()
        self.assertEqual(not_executed.status, ExecutionStatus.NOT_EXECUTED)
        self.assertEqual(failed.status, ExecutionStatus.FAILED)


class MetricsTests(unittest.TestCase):
    def test_event_metrics(self):
        events = [
            event(EventType.RETRY, {"reason": "transient", "attempt": 2}),
            event(EventType.REPLAN, {"reason": "new constraint", "attempt": 1}),
            event(EventType.EXECUTOR_STARTED, {"executor_id": "a"}),
            event(EventType.EXECUTOR_STARTED, {"executor_id": "a"}),
            event(EventType.HANDOFF, {"source_executor": "a", "target_executor": "b", "reason": "capacity"}),
            event(EventType.HUMAN_INTERVENTION, {"reason": "approval"}),
        ]
        record = collector(events).summarize()
        self.assertEqual(record.retry_count, 1)
        self.assertEqual(record.replan_count, 1)
        self.assertEqual(record.executor_invocations, 2)
        self.assertEqual(record.handoff_count, 1)
        self.assertEqual(record.human_interventions, 1)
        self.assertEqual(record.metadata["handoffs"][0]["target_executor"], "b")


class DeterminismTests(unittest.TestCase):
    def test_same_controlled_sequence_has_same_summary(self):
        first = build_baseline_record().to_json()
        second = build_baseline_record().to_json()
        self.assertEqual(first, second)


class UnknownMeasurementTests(unittest.TestCase):
    def test_unknown_tokens_and_cost_are_not_zero(self):
        record = collector([]).summarize()
        self.assertIsNone(record.total_tokens)
        self.assertIsNone(record.monetary_cost)

    def test_negative_or_non_finite_resource_measurements_are_rejected(self):
        with self.assertRaises(ValueError):
            collector([event(EventType.EXECUTOR_FINISHED, {"total_tokens": -1})]).summarize()
        with self.assertRaises(ValueError):
            collector([event(EventType.EXECUTOR_FINISHED, {"monetary_cost": float("inf")})]).summarize()

    def test_explicit_zero_is_preserved_as_zero(self):
        record = collector([event(EventType.EXECUTOR_FINISHED, {"total_tokens": 0, "monetary_cost": 0.0})]).summarize()
        self.assertEqual(record.total_tokens, 0)
        self.assertEqual(record.monetary_cost, 0.0)


class SerializationTests(unittest.TestCase):
    def test_record_json_round_trip_preserves_semantics(self):
        record = build_baseline_record()
        restored = type(record).from_json(record.to_json())
        self.assertEqual(restored.to_dict(), record.to_dict())

    def test_schema_is_versioned(self):
        self.assertEqual(build_baseline_record().to_dict()["schemaVersion"], 1)

    def test_record_can_be_written_to_a_local_artifact_path(self):
        record = build_baseline_record()
        with TemporaryDirectory() as directory:
            path = Path(directory) / "run.json"
            record.write_json(path)
            self.assertEqual(type(record).from_json(path.read_text(encoding="utf-8").strip()).to_dict(), record.to_dict())


class ValidationTests(unittest.TestCase):
    def test_events_from_another_run_are_rejected(self):
        value = TelemetryCollector(task_id="task", run_id=RUN_ID)
        with self.assertRaises(ValueError):
            value.add(event(EventType.TASK_STARTED, run_id="other"))

    def test_invalid_timestamps_are_rejected(self):
        with self.assertRaises(ValueError):
            collector([event(EventType.TASK_STARTED, timestamp="not-a-timestamp")])


if __name__ == "__main__":
    unittest.main()
