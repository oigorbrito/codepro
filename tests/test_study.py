import json
import unittest
from dataclasses import replace
from pathlib import Path

from arkx.study import (
    ComparisonMode,
    Methodology,
    RawResultsPolicy,
    StudySpec,
    freeze_study_spec,
    validate_study_spec,
)


def valid(**overrides):
    values = {
        "study_id": "study-routing-v1",
        "methodology": Methodology.ENGINEERING_RESEARCH_BENCHMARKING,
        "research_question": "Does bounded routing reduce cost without reducing verified resolution?",
        "hypothesis": "Bounded routing reduces median cost while preserving verified resolution.",
        "experimental_unit": "one benchmark task attempt",
        "quality_attribute": "cost-efficient reliable resolution",
        "workload_refs": ("benchmark://swebench/verified/pinned-set-v1",),
        "metrics": ("verified_resolution", "monetary_cost", "wall_time_ms"),
        "primary_metric": "verified_resolution",
        "comparison_mode": ComparisonMode.CONTROL_TREATMENT,
        "control_ref": "config://direct-v1",
        "treatment_refs": ("config://bounded-routing-v1",),
        "repetitions": 3,
        "repetition_justification": None,
        "stopping_rule": "run every frozen task/configuration/repetition unless externally blocked",
        "analysis_plan_ref": "analysis://routing-v1",
        "promotion_rule": "promote only if the frozen acceptance gate is satisfied",
        "environment_contract_ref": "env://arkx-ci-python-3.14.7-ubuntu-24.04",
        "raw_results_policy": RawResultsPolicy.PERSIST_ALL_RAW_RUNS,
    }
    values.update(overrides)
    return StudySpec(**values)


class ValidationTests(unittest.TestCase):
    def test_valid_spec_has_no_issues(self):
        self.assertEqual(validate_study_spec(valid()), ())

    def test_missing_workload_fails_closed(self):
        self.assertIn("workload_refs must contain at least one immutable or versioned reference", validate_study_spec(valid(workload_refs=())))

    def test_primary_metric_must_be_declared(self):
        self.assertIn("primary_metric must be included in metrics", validate_study_spec(valid(primary_metric="undeclared")))

    def test_control_and_treatment_must_be_distinct(self):
        issues = validate_study_spec(valid(treatment_refs=("config://direct-v1",)))
        self.assertIn("control_ref must be distinct from treatment_refs", issues)

    def test_single_run_requires_justification(self):
        issues = validate_study_spec(valid(repetitions=1, repetition_justification=None))
        self.assertIn("single-run studies require repetition_justification", issues)

    def test_no_comparator_requires_justification(self):
        issues = validate_study_spec(
            valid(
                comparison_mode=ComparisonMode.NO_COMPARATOR_JUSTIFIED,
                control_ref=None,
                treatment_refs=(),
                comparator_justification=None,
            )
        )
        self.assertIn("NO_COMPARATOR_JUSTIFIED requires comparator_justification", issues)


class FreezeTests(unittest.TestCase):
    def test_same_design_has_same_hash(self):
        first = freeze_study_spec(valid())
        second = freeze_study_spec(valid())
        self.assertEqual(first.to_json(), second.to_json())

    def test_design_change_changes_hash(self):
        first = freeze_study_spec(valid())
        second = freeze_study_spec(replace(valid(), repetitions=5))
        self.assertNotEqual(first.content_hash, second.content_hash)

    def test_invalid_spec_cannot_be_frozen(self):
        with self.assertRaises(ValueError):
            freeze_study_spec(valid(workload_refs=()))

    def test_round_trip_preserves_semantics(self):
        spec = valid()
        restored = StudySpec.from_json(spec.to_json())
        self.assertEqual(restored.to_dict(), spec.to_dict())

    def test_spec_contains_no_result_or_pass_state(self):
        serialized = freeze_study_spec(valid()).to_json()
        self.assertNotIn('"result"', serialized)
        self.assertNotIn('"PASS"', serialized)


class FixtureTests(unittest.TestCase):
    def test_fixture_is_a_pre_execution_design_not_a_result(self):
        path = Path(__file__).parents[1] / "experiments" / "study-spec-fixture.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(value["fixture_type"], "STUDY_SPEC_FIXTURE")
        spec = StudySpec.from_dict(value["study_spec"])
        self.assertEqual(validate_study_spec(spec), ())
        self.assertEqual(freeze_study_spec(spec).content_hash, value["expected_content_hash"])


if __name__ == "__main__":
    unittest.main()
