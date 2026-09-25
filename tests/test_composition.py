import json
import unittest
from pathlib import Path

from arkx.composition import (
    ComparabilityStatus,
    ExperimentIdentity,
    ExperimentManifest,
    Mechanism,
    Treatment,
    TrialObservation,
    compare_trials,
    initial_manifest,
    summarize_trials,
)


def identity(**overrides):
    values = {
        "task": "task-1",
        "executor": "executor-1",
        "model": "model-1",
        "environment": "env-1",
        "budget": "budget-1",
    }
    values.update(overrides)
    return ExperimentIdentity(**values)


class CompositionTests(unittest.TestCase):
    def test_mechanism_order_is_canonical(self):
        treatment = Treatment("D", (Mechanism.P3_ROUTING, Mechanism.P1_CHARACTERIZATION, Mechanism.P2_PROGRESS))
        self.assertEqual(
            treatment.enabled_mechanisms,
            (Mechanism.P1_CHARACTERIZATION, Mechanism.P2_PROGRESS, Mechanism.P3_ROUTING),
        )

    def test_initial_manifest_contains_only_a_to_f(self):
        self.assertEqual(tuple(t.name for t in initial_manifest().treatments), ("A", "B", "C", "D", "E", "F"))

    def test_duplicate_names_are_invalid(self):
        with self.assertRaises(ValueError):
            ExperimentManifest((Treatment("A", ()), Treatment("A", (Mechanism.P1_CHARACTERIZATION,))))

    def test_duplicate_semantic_compositions_are_invalid(self):
        with self.assertRaises(ValueError):
            ExperimentManifest((Treatment("A", ()), Treatment("another-name", ())))

    def test_input_order_has_same_canonical_json(self):
        left = Treatment("C", (Mechanism.P2_PROGRESS, Mechanism.P1_CHARACTERIZATION))
        right = Treatment("C", (Mechanism.P1_CHARACTERIZATION, Mechanism.P2_PROGRESS))
        self.assertEqual(left.to_dict(), right.to_dict())

    def test_each_control_dimension_divergence_is_incomparable(self):
        base = identity()
        trial = TrialObservation(base, Treatment("A", ()))
        for field in ("task", "executor", "model", "environment", "budget"):
            divergent = identity(**{field: f"different-{field}"})
            self.assertEqual(compare_trials(trial, TrialObservation(divergent, Treatment("B", ()))), ComparabilityStatus.INCOMPARABLE)

    def test_missing_control_dimension_is_unknown(self):
        trial = TrialObservation(identity(), Treatment("A", ()))
        missing = TrialObservation(identity(model=None), Treatment("B", ()))
        self.assertEqual(compare_trials(trial, missing), ComparabilityStatus.UNKNOWN)

    def test_summary_does_not_impute_missing_measurements(self):
        summary = summarize_trials((TrialObservation(identity(), Treatment("A", ()), (("tokens", 12),)),))
        self.assertEqual(summary.measurement_counts, (("tokens", 1),))
        self.assertNotIn("cost", summary.to_json())

    def test_summary_is_deterministic_and_never_pass(self):
        trials = (
            TrialObservation(identity(), Treatment("B", (Mechanism.P1_CHARACTERIZATION,)), (("wall_time_ms", 4),)),
            TrialObservation(identity(), Treatment("A", ()), (("wall_time_ms", 5),)),
        )
        first = summarize_trials(trials)
        second = summarize_trials(tuple(reversed(trials)))
        self.assertEqual(first.to_json(), second.to_json())
        self.assertNotIn("PASS", first.to_json())

    def test_measurements_are_sorted_and_unique(self):
        trial = TrialObservation(identity(), Treatment("A", ()), (("z", 1), ("a", 2)))
        self.assertEqual(tuple(key for key, _ in trial.measurements), ("a", "z"))
        with self.assertRaises(ValueError):
            TrialObservation(identity(), Treatment("A", ()), (("a", 1), ("a", 2)))

    def test_fixture_is_classified_as_composition_fixture(self):
        path = Path(__file__).parents[1] / "experiments" / "composition-harness-fixture.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(value["fixture_type"], "EXPERIMENTAL_COMPOSITION_FIXTURE")
        self.assertEqual(value["treatments"], ["A", "B", "C", "D", "E", "F"])


if __name__ == "__main__":
    unittest.main()
