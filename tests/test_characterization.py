import unittest
import json
from pathlib import Path

from arkx.characterization import (
    Confidence,
    RecommendedPath,
    Scope,
    TaskSignals,
    characterize,
    characterize_timed,
)
from arkx.contracts import ExecutionStatus
from arkx.telemetry import TelemetryCollector


def complete_signals(**overrides):
    values = {
        "candidate_files": ("src/one.py",),
        "dependency_edges": (),
        "affected_components": ("one",),
        "known_tests": ("tests/test_one.py",),
        "ambiguity_markers": (),
        "risk_markers": (),
        "acceptance_checks": ("tests pass",),
        "state_shared": False,
        "architectural_change": False,
    }
    values.update(overrides)
    return TaskSignals(**values)


class ClassificationTests(unittest.TestCase):
    def test_single_file_is_simple(self):
        result = characterize(complete_signals())
        self.assertEqual(result.scope, Scope.SIMPLE)
        self.assertEqual(result.recommended_path, RecommendedPath.SIMPLE_PATH)
        self.assertEqual(result.confidence, Confidence.HIGH)

    def test_bounded_few_file_task_is_localized(self):
        result = characterize(
            complete_signals(
                candidate_files=("src/one.py", "tests/test_one.py"),
                dependency_edges=(("one", "contracts"),),
                acceptance_checks=("tests pass", "round-trip passes"),
            )
        )
        self.assertEqual(result.scope, Scope.LOCALIZED)
        self.assertEqual(result.recommended_path, RecommendedPath.LOCALIZED_PATH)

    def test_cross_component_change_is_repository_wide(self):
        result = characterize(
            complete_signals(
                candidate_files=("a.py", "b.py", "c.py", "d.py", "e.py", "f.py"),
                dependency_edges=(("a", "b"), ("b", "c"), ("c", "shared"), ("tests", "a")),
                affected_components=("a", "b", "c"),
                known_tests=("a", "b", "c"),
                state_shared=True,
                architectural_change=True,
            )
        )
        self.assertEqual(result.scope, Scope.REPOSITORY_WIDE)
        self.assertEqual(result.recommended_path, RecommendedPath.REPOSITORY_WIDE_PATH)
        self.assertEqual(result.confidence, Confidence.MEDIUM)

    def test_insufficient_signals_are_unknown_and_require_qualification(self):
        result = characterize(TaskSignals(ambiguity_markers=("unclear",)))
        self.assertEqual(result.scope, Scope.UNKNOWN)
        self.assertEqual(result.recommended_path, RecommendedPath.QUALIFICATION_REQUIRED)
        self.assertEqual(result.confidence, Confidence.LOW)

    def test_contradictory_signals_require_qualification(self):
        result = characterize(complete_signals(declared_scope=Scope.REPOSITORY_WIDE))
        self.assertEqual(result.scope, Scope.UNKNOWN)
        self.assertEqual(result.recommended_path, RecommendedPath.QUALIFICATION_REQUIRED)
        self.assertIn("CONTRADICTORY_SIGNALS", [value.value for value in result.signals])


class EvidenceAndDeterminismTests(unittest.TestCase):
    def test_signal_order_does_not_change_serialization(self):
        first = complete_signals(
            candidate_files=("b.py", "a.py"),
            dependency_edges=(("b", "c"), ("a", "b")),
            affected_components=("two", "one"),
            known_tests=("z", "a"),
            acceptance_checks=("second", "first"),
        )
        second = complete_signals(
            candidate_files=("a.py", "b.py"),
            dependency_edges=(("a", "b"), ("b", "c")),
            affected_components=("one", "two"),
            known_tests=("a", "z"),
            acceptance_checks=("first", "second"),
        )
        self.assertEqual(characterize(first).to_json(), characterize(second).to_json())

    def test_controlled_duration_is_serialized_as_telemetry(self):
        result = characterize(complete_signals(), characterization_duration_ms=7)
        self.assertEqual(result.telemetry["characterization_duration_ms"], 7)
        self.assertEqual(result.telemetry["signal_count"], 7)

    def test_timed_characterization_reports_nonnegative_duration(self):
        result = characterize_timed(complete_signals())
        self.assertGreaterEqual(result.telemetry["characterization_duration_ms"], 0)

    def test_characterization_alone_cannot_produce_pass(self):
        result = characterize(complete_signals())
        self.assertNotIn("status", result.to_dict())
        execution = TelemetryCollector(task_id="task", run_id="run").summarize()
        self.assertEqual(execution.status, ExecutionStatus.NOT_EXECUTED)

    def test_synthetic_fixture_covers_the_four_declared_categories(self):
        manifest_path = Path(__file__).parents[1] / "experiments" / "characterization-fixture.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["fixture_type"], "CHARACTERIZATION_FIXTURE")
        observed = {}
        for task in manifest["tasks"]:
            raw = task["signals"]
            signals = TaskSignals(
                candidate_files=None if raw["candidate_files"] is None else tuple(raw["candidate_files"]),
                dependency_edges=None if raw["dependency_edges"] is None else tuple(tuple(edge) for edge in raw["dependency_edges"]),
                affected_components=None if raw["affected_components"] is None else tuple(raw["affected_components"]),
                known_tests=None if raw["known_tests"] is None else tuple(raw["known_tests"]),
                ambiguity_markers=None if raw["ambiguity_markers"] is None else tuple(raw["ambiguity_markers"]),
                risk_markers=None if raw["risk_markers"] is None else tuple(raw["risk_markers"]),
                acceptance_checks=None if raw["acceptance_checks"] is None else tuple(raw["acceptance_checks"]),
                state_shared=raw.get("state_shared"),
                architectural_change=raw.get("architectural_change"),
            )
            observed[task["id"]] = characterize(signals).scope.value
        self.assertEqual(observed, {
            "simple": "SIMPLE",
            "localized": "LOCALIZED",
            "repository-wide": "REPOSITORY_WIDE",
            "ambiguous": "UNKNOWN",
        })


if __name__ == "__main__":
    unittest.main()
