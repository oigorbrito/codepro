import json
import unittest
from pathlib import Path

from arkx.contracts import ExecutionStatus
from arkx.progress import (
    Confidence,
    ProgressSnapshot,
    ProgressStatus,
    ReasonCode,
    assess_progress,
    assess_progress_timed,
)
from arkx.telemetry import TelemetryCollector


def snapshot(**overrides):
    values = {
        "useful_files": ("src/a.py",),
        "passing_tests": (),
        "explained_failures": (),
        "diff_distance": 4,
        "acceptance_distance": 3,
        "recent_actions": ("inspect a",),
        "failure_signatures": ("failure-a",),
    }
    values.update(overrides)
    return ProgressSnapshot(**values)


class StatusTests(unittest.TestCase):
    def test_new_passing_test_proves_progress(self):
        result = assess_progress(snapshot(), snapshot(passing_tests=("test_a",)))
        self.assertEqual(result.status, ProgressStatus.PROGRESS_PROVEN)
        self.assertIn(ReasonCode.NEW_PASSING_TEST, result.reason_codes)

    def test_new_relevant_file_proves_progress(self):
        result = assess_progress(snapshot(), snapshot(useful_files=("src/a.py", "src/b.py")))
        self.assertEqual(result.status, ProgressStatus.PROGRESS_PROVEN)

    def test_same_failure_and_no_new_evidence_is_no_progress(self):
        result = assess_progress(snapshot(), snapshot())
        self.assertEqual(result.status, ProgressStatus.NO_PROGRESS)
        self.assertIn(ReasonCode.REPEATED_FAILURE_SIGNATURE, result.reason_codes)
        self.assertIn(ReasonCode.NO_NEW_EVIDENCE, result.reason_codes)

    def test_repeated_action_and_unchanged_acceptance_is_no_progress(self):
        result = assess_progress(snapshot(failure_signatures=()), snapshot(failure_signatures=()))
        self.assertEqual(result.status, ProgressStatus.NO_PROGRESS)
        self.assertIn(ReasonCode.REPEATED_ACTION, result.reason_codes)

    def test_new_failure_with_new_evidence_is_not_no_progress(self):
        result = assess_progress(
            snapshot(failure_signatures=("failure-a",)),
            snapshot(useful_files=("src/a.py", "src/b.py"), failure_signatures=("failure-b",)),
        )
        self.assertEqual(result.status, ProgressStatus.PROGRESS_PROVEN)
        self.assertNotEqual(result.status, ProgressStatus.NO_PROGRESS)

    def test_missing_measurement_is_unknown(self):
        result = assess_progress(None, ProgressSnapshot())
        self.assertEqual(result.status, ProgressStatus.UNKNOWN)
        self.assertEqual(result.confidence, Confidence.LOW)

    def test_contradictory_distance_is_unknown(self):
        result = assess_progress(snapshot(diff_distance=-1), snapshot(diff_distance=0))
        self.assertEqual(result.status, ProgressStatus.UNKNOWN)
        self.assertIn(ReasonCode.CONTRADICTORY_SIGNALS, result.reason_codes)


class DeterminismTests(unittest.TestCase):
    def test_same_snapshots_are_byte_equivalent(self):
        first = assess_progress(snapshot(), snapshot(useful_files=("src/a.py", "src/b.py")), assessment_duration_ms=4)
        second = assess_progress(snapshot(), snapshot(useful_files=("src/b.py", "src/a.py")), assessment_duration_ms=4)
        self.assertEqual(first.to_json(), second.to_json())

    def test_timed_assessment_reports_duration(self):
        result = assess_progress_timed(snapshot(), snapshot())
        self.assertGreaterEqual(result.telemetry["assessment_duration_ms"], 0)

    def test_assessment_does_not_produce_pass_or_change_p0(self):
        result = assess_progress(snapshot(), snapshot())
        self.assertNotIn("PASS", result.to_json())
        execution = TelemetryCollector(task_id="task", run_id="run").summarize()
        self.assertEqual(execution.status, ExecutionStatus.NOT_EXECUTED)

    def test_synthetic_fixture_covers_all_sequences(self):
        path = Path(__file__).parents[1] / "experiments" / "progress-detection-fixture.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["fixture_type"], "PROGRESS_DETECTION_FIXTURE")
        observed = {}
        for sequence in manifest["sequences"]:
            previous = None if sequence["previous"] is None else ProgressSnapshot(**_snapshot_values(sequence["previous"]))
            current = ProgressSnapshot(**_snapshot_values(sequence["current"]))
            observed[sequence["id"]] = assess_progress(previous, current).status.value
        self.assertEqual(observed, {
            "A_productive_progression": "PROGRESS_PROVEN",
            "B_repeated_failure_without_new_evidence": "NO_PROGRESS",
            "C_partial_progress": "PROGRESS_PROVEN",
            "D_unknown_missing_telemetry": "UNKNOWN",
            "E_contradictory_signals": "UNKNOWN",
        })


def _snapshot_values(value):
    return {
        "useful_files": None if value["useful_files"] is None else tuple(value["useful_files"]),
        "passing_tests": None if value["passing_tests"] is None else tuple(value["passing_tests"]),
        "explained_failures": None if value["explained_failures"] is None else tuple(value["explained_failures"]),
        "diff_distance": value["diff_distance"],
        "acceptance_distance": value["acceptance_distance"],
        "recent_actions": None if value["recent_actions"] is None else tuple(value["recent_actions"]),
        "failure_signatures": None if value["failure_signatures"] is None else tuple(value["failure_signatures"]),
    }


if __name__ == "__main__":
    unittest.main()

