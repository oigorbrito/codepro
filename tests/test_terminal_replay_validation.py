import unittest

from arkx.event_log import ReplayState, validate_terminal_replay


class TerminalReplayValidationTests(unittest.TestCase):
    def test_terminal_status_and_error_are_checked(self):
        replay = ReplayState("run-1", 1, declared_status="BLOCKED", error_codes=("SANDBOX_UNAVAILABLE",))
        validate_terminal_replay(replay, expected_status="BLOCKED", expected_error_code="SANDBOX_UNAVAILABLE")

    def test_missing_terminal_is_not_inferred(self):
        with self.assertRaises(ValueError):
            validate_terminal_replay(ReplayState("run-1", 0), expected_status="COMPLETED")

    def test_wrong_terminal_error_is_rejected(self):
        replay = ReplayState("run-1", 1, declared_status="BLOCKED", error_codes=("A",))
        with self.assertRaises(ValueError):
            validate_terminal_replay(replay, expected_status="BLOCKED", expected_error_code="B")
