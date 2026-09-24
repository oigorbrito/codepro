import json
import unittest
from dataclasses import replace
from pathlib import Path

from arkx.analysis_plan import (
    AnalysisDesign,
    AnalysisPlan,
    InferenceMode,
    freeze_analysis_plan,
    validate_analysis_compatibility,
    validate_analysis_plan,
)
from arkx.study import ComparisonMode, Methodology, StudySpec, freeze_study_spec


def study():
    return StudySpec(
        study_id="study-routing-v1",
        methodology=Methodology.ENGINEERING_RESEARCH_BENCHMARKING,
        research_question="Does bounded routing improve cost efficiency without reducing verified resolution?",
        hypothesis="Bounded routing preserves verified resolution while reducing cost.",
        experimental_unit="task attempt",
        quality_attribute="cost-efficient reliable resolution",
        workload_refs=("benchmark://frozen",),
        metrics=("verified_resolution", "monetary_cost", "wall_time_ms"),
        primary_metric="verified_resolution",
        comparison_mode=ComparisonMode.CONTROL_TREATMENT,
        control_ref="config://direct",
        treatment_refs=("config://routing",),
        repetitions=3,
        stopping_rule="complete the frozen matrix unless externally blocked",
        analysis_plan_ref="analysis://routing-v1",
        promotion_rule="use frozen gate",
        environment_contract_ref="env://frozen",
    )


def frozen_study():
    return freeze_study_spec(study())


def valid(**overrides):
    values = {
        "analysis_id": "analysis-routing-v1",
        "design": AnalysisDesign.PAIRED,
        "primary_metric": "verified_resolution",
        "secondary_metrics": ("monetary_cost", "wall_time_ms"),
        "estimand": "paired treatment-minus-control effect over the frozen workload",
        "summary_statistics": ("proportion", "median", "iqr"),
        "inference_mode": InferenceMode.FREQUENTIST,
        "uncertainty_method": "paired bootstrap confidence interval",
        "confidence_level": 0.95,
        "analysis_population_rule": "all frozen task/configuration/repetition cells with raw manifests",
        "missing_data_rule": "do not impute; report missingness by reason and configuration",
        "blocked_run_rule": "BLOCKED remains a separate outcome and is not converted to failure or success",
        "protocol_deviation_rule": "analyze deviations separately and report both frozen-set and sensitivity views",
        "multiplicity_rule": "primary metric is confirmatory; secondary metrics are descriptive unless corrected",
        "outlier_rule": "retain all valid runs; no outcome-based trimming",
        "analysis_script_ref": "analysis-script://routing-v1",
    }
    values.update(overrides)
    return AnalysisPlan(**values)


class ValidationTests(unittest.TestCase):
    def test_valid_plan_has_no_issues(self):
        self.assertEqual(validate_analysis_plan(valid()), ())

    def test_frequentist_plan_requires_valid_confidence_level(self):
        self.assertIn(
            "FREQUENTIST analysis requires confidence_level strictly between 0 and 1",
            validate_analysis_plan(valid(confidence_level=1.5)),
        )

    def test_descriptive_design_cannot_smuggle_in_inference(self):
        issues = validate_analysis_plan(
            valid(design=AnalysisDesign.DESCRIPTIVE_ONLY, inference_mode=InferenceMode.FREQUENTIST)
        )
        self.assertIn("DESCRIPTIVE_ONLY design requires inference_mode NONE", issues)

    def test_primary_metric_cannot_be_secondary_too(self):
        self.assertIn(
            "primary_metric must not be duplicated in secondary_metrics",
            validate_analysis_plan(valid(secondary_metrics=("verified_resolution",))),
        )


class CompatibilityTests(unittest.TestCase):
    def test_primary_metric_must_match_study(self):
        issues = validate_analysis_compatibility(valid(primary_metric="monetary_cost"), study())
        self.assertIn("analysis primary_metric must match frozen Study Spec primary_metric", issues)

    def test_secondary_metric_must_be_declared_in_study(self):
        issues = validate_analysis_compatibility(valid(secondary_metrics=("invented_metric",)), study())
        self.assertTrue(any("undeclared secondary metrics" in issue for issue in issues))


class FreezeTests(unittest.TestCase):
    def test_same_plan_has_same_hash(self):
        self.assertEqual(
            freeze_analysis_plan(valid(), frozen_study()).to_json(),
            freeze_analysis_plan(valid(), frozen_study()).to_json(),
        )

    def test_rule_change_changes_hash(self):
        first = freeze_analysis_plan(valid(), frozen_study())
        second = freeze_analysis_plan(replace(valid(), outlier_rule="different frozen rule"), frozen_study())
        self.assertNotEqual(first.content_hash, second.content_hash)

    def test_invalid_plan_cannot_be_frozen(self):
        with self.assertRaises(ValueError):
            freeze_analysis_plan(valid(primary_metric="undeclared"), frozen_study())


    def test_frozen_plan_records_governing_study_hash(self):
        frozen = freeze_analysis_plan(valid(), frozen_study())
        self.assertEqual(frozen.study_spec_hash, frozen_study().content_hash)

    def test_compatible_study_change_changes_frozen_identity(self):
        first = freeze_analysis_plan(valid(), frozen_study())
        changed_study = freeze_study_spec(replace(study(), hypothesis="a changed frozen hypothesis"))
        second = freeze_analysis_plan(valid(), changed_study)
        self.assertNotEqual(first.content_hash, second.content_hash)


class FixtureTests(unittest.TestCase):
    def test_fixture_is_pre_execution_analysis_design(self):
        path = Path(__file__).parents[1] / "experiments" / "analysis-plan-fixture.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        plan = AnalysisPlan.from_dict(value["analysis_plan"])
        self.assertEqual(value["fixture_type"], "ANALYSIS_PLAN_FIXTURE")
        self.assertEqual(validate_analysis_plan(plan), ())
        self.assertNotIn("observed_results", value)


if __name__ == "__main__":
    unittest.main()
