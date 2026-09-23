import json
import unittest
from dataclasses import replace
from pathlib import Path

from arkx.study import ComparisonMode, Methodology, StudySpec
from arkx.validity import (
    ConstructMapping,
    Threat,
    ValidityDimension,
    ValidityPlan,
    freeze_validity_plan,
    validate_validity_compatibility,
    validate_validity_plan,
)


def study():
    return StudySpec(
        study_id="study-v1",
        methodology=Methodology.ENGINEERING_RESEARCH_BENCHMARKING,
        research_question="Does routing improve efficiency without reducing verified resolution?",
        hypothesis="Routing preserves verified resolution while reducing cost.",
        experimental_unit="task attempt",
        quality_attribute="cost-efficient reliable resolution",
        workload_refs=("workload://wave0",),
        metrics=("verified_resolution", "monetary_cost"),
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


def threat(identifier, dimension):
    return Threat(
        threat_id=identifier,
        dimension=dimension,
        claim_at_risk="the comparative claim",
        mechanism="the stated threat can distort the observed comparison",
        mitigation="freeze and report the relevant design choice",
        residual_risk="generalization remains bounded to the declared scope",
    )


def valid(**overrides):
    values = {
        "validity_id": "validity-v1",
        "workload_refs": ("workload://wave0",),
        "target_population": "repository-level repair tasks within the declared benchmark scope",
        "workload_representativeness_argument": "the frozen workload samples the benchmark population under treatment-independent criteria",
        "artifact_strengths": ("explicit fail-closed evidence semantics",),
        "artifact_weaknesses": ("rule-based routing may not fit all task distributions",),
        "artifact_limitations": ("claims do not extend beyond the frozen benchmark population without further evidence",),
        "state_of_art_alternative_refs": ("alternative://direct-execution",),
        "no_alternative_justification": None,
        "construct_mappings": (
            ConstructMapping("verified_resolution", "reliable task resolution", "independent verifier outcome", "benchmark verifier coverage is imperfect"),
            ConstructMapping("monetary_cost", "resource efficiency", "provider-reported monetary cost", "provider accounting may omit external costs"),
        ),
        "threats": (
            threat("construct-1", ValidityDimension.CONSTRUCT),
            threat("external-1", ValidityDimension.EXTERNAL),
            threat("conclusion-1", ValidityDimension.CONCLUSION),
            threat("repro-1", ValidityDimension.RELIABILITY_REPRODUCIBILITY),
        ),
    }
    values.update(overrides)
    return ValidityPlan(**values)


class ValidationTests(unittest.TestCase):
    def test_valid_plan_has_no_issues(self):
        self.assertEqual(validate_validity_plan(valid()), ())

    def test_generic_threat_list_without_required_dimensions_fails(self):
        issues = validate_validity_plan(valid(threats=(threat("construct", ValidityDimension.CONSTRUCT),)))
        self.assertTrue(any("missing required validity dimensions" in issue for issue in issues))

    def test_alternatives_or_justification_required(self):
        issues = validate_validity_plan(
            valid(state_of_art_alternative_refs=(), no_alternative_justification=None)
        )
        self.assertIn(
            "state-of-art alternatives or an explicit no-alternative justification are required",
            issues,
        )

    def test_strength_weakness_and_limit_are_explicit(self):
        self.assertIn(
            "artifact_weaknesses must explicitly describe at least one weakness",
            validate_validity_plan(valid(artifact_weaknesses=())),
        )


class CompatibilityTests(unittest.TestCase):
    def test_every_study_metric_requires_construct_mapping(self):
        mappings = (ConstructMapping("verified_resolution", "resolution", "reason", "limit"),)
        issues = validate_validity_compatibility(valid(construct_mappings=mappings), study())
        self.assertTrue(any("missing construct mapping" in issue for issue in issues))

    def test_workload_reference_must_match_study(self):
        issues = validate_validity_compatibility(valid(workload_refs=("workload://other",)), study())
        self.assertIn("validity workload_refs must match frozen Study Spec workload_refs", issues)


class FreezeTests(unittest.TestCase):
    def test_same_plan_has_same_hash(self):
        self.assertEqual(
            freeze_validity_plan(valid(), study()).to_json(),
            freeze_validity_plan(valid(), study()).to_json(),
        )

    def test_claim_change_changes_hash(self):
        first = freeze_validity_plan(valid(), study())
        second = freeze_validity_plan(
            replace(valid(), target_population="a different population"),
            study(),
        )
        self.assertNotEqual(first.content_hash, second.content_hash)


class FixtureTests(unittest.TestCase):
    def test_fixture_contains_claim_linked_threats(self):
        path = Path(__file__).parents[1] / "experiments" / "validity-plan-fixture.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        plan = ValidityPlan.from_dict(value["validity_plan"])
        self.assertEqual(value["fixture_type"], "VALIDITY_PLAN_FIXTURE")
        self.assertEqual(validate_validity_plan(plan), ())


if __name__ == "__main__":
    unittest.main()
