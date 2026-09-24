import json
import unittest
from dataclasses import replace
from pathlib import Path

from arkx.measurement import (
    Direction,
    MeasurementContract,
    MetricDataType,
    MetricDefinition,
    freeze_measurement_contract,
    validate_measurement_compatibility,
    validate_measurement_contract,
)
from arkx.study import ComparisonMode, Methodology, StudySpec, freeze_study_spec


def metric(identifier, *, unit="observation", direction=Direction.NONE):
    return MetricDefinition(
        metric_id=identifier,
        data_type=MetricDataType.FLOAT,
        unit=unit,
        direction=direction,
        source="raw execution record or independent verifier",
        measurement_rule=f"measure {identifier} once per valid frozen run",
        missing_semantics="unknown or unobserved is JSON null and is never coerced to zero",
        invalid_semantics="invalid runs remain invalid and do not receive a fabricated measurement",
        precision_rule="preserve source precision in raw data; round only for display",
    )


def study():
    return StudySpec(
        study_id="study-v1",
        methodology=Methodology.ENGINEERING_RESEARCH_BENCHMARKING,
        research_question="Does routing improve efficiency without reducing resolution?",
        hypothesis="Routing preserves resolution and reduces cost.",
        experimental_unit="task attempt",
        quality_attribute="cost-efficient reliable resolution",
        workload_refs=("workload://v1",),
        metrics=("verified_resolution", "monetary_cost", "wall_time_ms"),
        primary_metric="verified_resolution",
        comparison_mode=ComparisonMode.CONTROL_TREATMENT,
        control_ref="config://direct",
        treatment_refs=("config://routing",),
        repetitions=3,
        stopping_rule="frozen matrix",
        analysis_plan_ref="analysis://v1",
        promotion_rule="frozen gate",
        environment_contract_ref="env://v1",
    )


def frozen_study():
    return freeze_study_spec(study())


def valid(**overrides):
    values = {
        "measurement_id": "measurement-v1",
        "metrics": (
            metric("verified_resolution", unit="boolean", direction=Direction.HIGHER_IS_BETTER),
            metric("monetary_cost", unit="USD", direction=Direction.LOWER_IS_BETTER),
            metric("wall_time_ms", unit="milliseconds", direction=Direction.LOWER_IS_BETTER),
        ),
    }
    values.update(overrides)
    return MeasurementContract(**values)


class ValidationTests(unittest.TestCase):
    def test_valid_contract_has_no_issues(self):
        self.assertEqual(validate_measurement_contract(valid()), ())

    def test_duplicate_metric_ids_are_rejected(self):
        issues = validate_measurement_contract(valid(metrics=(metric("a"), metric("a"))))
        self.assertIn("metric_id values must be unique", issues)

    def test_missing_semantics_must_be_explicit(self):
        bad = replace(metric("cost"), missing_semantics="omit it")
        issues = validate_measurement_contract(valid(metrics=(bad,)))
        self.assertTrue(any("missing_semantics" in issue for issue in issues))

    def test_study_metric_requires_definition(self):
        issues = validate_measurement_compatibility(
            valid(metrics=(metric("verified_resolution"),)),
            study(),
        )
        self.assertTrue(any("study metrics lack operational definitions" in issue for issue in issues))


class FreezeTests(unittest.TestCase):
    def test_same_contract_has_same_hash(self):
        self.assertEqual(
            freeze_measurement_contract(valid(), frozen_study()).to_json(),
            freeze_measurement_contract(valid(), frozen_study()).to_json(),
        )

    def test_measurement_rule_change_changes_identity(self):
        original = valid()
        first = freeze_measurement_contract(original, frozen_study())
        changed_metric = replace(original.metrics[0], measurement_rule="a changed operational definition")
        second = freeze_measurement_contract(
            replace(original, metrics=(changed_metric,) + original.metrics[1:]),
            frozen_study(),
        )
        self.assertNotEqual(first.content_hash, second.content_hash)


    def test_frozen_contract_records_governing_study_hash(self):
        frozen = freeze_measurement_contract(valid(), frozen_study())
        self.assertEqual(frozen.study_spec_hash, frozen_study().content_hash)

    def test_compatible_study_change_changes_frozen_identity(self):
        first = freeze_measurement_contract(valid(), frozen_study())
        changed_study = freeze_study_spec(replace(study(), hypothesis="a changed frozen hypothesis"))
        second = freeze_measurement_contract(valid(), changed_study)
        self.assertNotEqual(first.content_hash, second.content_hash)


class FixtureTests(unittest.TestCase):
    def test_fixture_defines_all_metrics_without_unknown_as_zero(self):
        path = Path(__file__).parents[1] / "experiments" / "measurement-contract-fixture.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        contract = MeasurementContract.from_dict(value["contract"])
        self.assertEqual(value["fixture_type"], "MEASUREMENT_CONTRACT_FIXTURE")
        self.assertEqual(validate_measurement_contract(contract), ())
        self.assertTrue(all("zero" in metric.missing_semantics.lower() for metric in contract.metrics))


if __name__ == "__main__":
    unittest.main()
