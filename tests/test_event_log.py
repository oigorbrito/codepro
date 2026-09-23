import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from arkx.contracts import Event, EventType
from arkx.event_log import EventLog


class EventLogTests(unittest.TestCase):
    def test_event_log_round_trips_and_appends_in_order(self):
        with TemporaryDirectory() as directory:
            log = EventLog(Path(directory) / "events.jsonl", run_id="run-1")
            log.append(Event("2026-01-01T00:00:00+00:00", EventType.TASK_STARTED, "run-1"))
            log.append(Event("2026-01-01T00:00:01+00:00", EventType.TASK_FINISHED, "run-1", {"status": "BLOCKED"}))
            self.assertEqual([event.type for event in log.read()], [EventType.TASK_STARTED, EventType.TASK_FINISHED])

    def test_event_log_rejects_wrong_run_and_time_regression(self):
        with TemporaryDirectory() as directory:
            log = EventLog(Path(directory) / "events.jsonl", run_id="run-1")
            log.append(Event("2026-01-01T00:00:01+00:00", EventType.TASK_STARTED, "run-1"))
            with self.assertRaises(ValueError):
                log.append(Event("2026-01-01T00:00:02+00:00", EventType.RETRY, "run-2"))
            with self.assertRaises(ValueError):
                log.append(Event("2025-01-01T00:00:00+00:00", EventType.RETRY, "run-1"))

    def test_stage_append_is_causal_and_idempotent(self):
        with TemporaryDirectory() as directory:
            log = EventLog(Path(directory) / "events.jsonl", run_id="run-1")
            self.assertTrue(log.append_stage(timestamp="2026-01-01T00:00:00+00:00", event_type=EventType.EVIDENCE_ADDED, stage="verification", ref="verification://1"))
            self.assertFalse(log.append_stage(timestamp="2026-01-01T00:00:01+00:00", event_type=EventType.EVIDENCE_ADDED, stage="verification", ref="verification://1"))
            with self.assertRaises(ValueError):
                log.append_stage(timestamp="2026-01-01T00:00:02+00:00", event_type=EventType.EVIDENCE_ADDED, stage="verification", ref="verification://2")


if __name__ == "__main__":
    unittest.main()
