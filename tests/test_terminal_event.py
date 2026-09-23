import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from arkx.contracts import EventType
from arkx.event_log import EventLog, replay_events


class TerminalEventTests(unittest.TestCase):
    def test_terminal_event_is_idempotent_and_replayable(self):
        with TemporaryDirectory() as directory:
            log = EventLog(Path(directory) / "events.jsonl", run_id="run-1")
            self.assertTrue(log.append_terminal(timestamp="2026-01-01T00:00:00+00:00", status="BLOCKED", error_code="SANDBOX_UNAVAILABLE"))
            self.assertFalse(log.append_terminal(timestamp="2026-01-01T00:00:01+00:00", status="BLOCKED", error_code="SANDBOX_UNAVAILABLE"))
            replay = replay_events(log.read(), run_id="run-1")
        self.assertEqual(replay.declared_status, "BLOCKED")
        self.assertEqual(replay.error_codes, ("SANDBOX_UNAVAILABLE",))

    def test_terminal_status_cannot_change(self):
        with TemporaryDirectory() as directory:
            log = EventLog(Path(directory) / "events.jsonl", run_id="run-1")
            log.append_terminal(timestamp="2026-01-01T00:00:00+00:00", status="FAILED")
            with self.assertRaises(ValueError):
                log.append_terminal(timestamp="2026-01-01T00:00:01+00:00", status="COMPLETED")

    def test_terminal_error_code_cannot_change(self):
        with TemporaryDirectory() as directory:
            log = EventLog(Path(directory) / "events.jsonl", run_id="run-1")
            log.append_terminal(timestamp="2026-01-01T00:00:00+00:00", status="BLOCKED", error_code="A")
            with self.assertRaises(ValueError):
                log.append_terminal(timestamp="2026-01-01T00:00:01+00:00", status="BLOCKED", error_code="B")


if __name__ == "__main__":
    unittest.main()
