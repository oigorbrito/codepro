import json
import unittest
from dataclasses import replace
from pathlib import Path

from arkx.promotion import (
    CriterionOperator,
    GateStatus,
    PromotionCriterion,
    PromotionDecisionStatus,
    PromotionGate,
    assess_promotion_gate,
    freeze_promotion_gate,
    record_promotion_decision,
    validate_promotion_gate,
)


def valid_gate(**overrides):
    values = {
        "gate_id": "routing-promotion-v1",
        "criteria": (
            PromotionCriterion(
                "resolution-nondegradation",
                "verified_resolution_delta",
                CriterionOperator.GTE,
                -0.01,
                "verified resolution may not materially degrade",
            ),
            PromotionCriterion(
                "cost-ceiling",
                "median_cost_ratio",
                CriterionOperator.LTE,
                1.0,
                "promotion requires no increase in median cost",
            ),
        ),
        "required_evidence_keys": (
            "analysis",
            "validity",
            "raw_run_completeness",
        ),
    }
    values.update(overrides)
    return PromotionGate(**values)


def frozen_gate():
    return freeze_promotion_gate(valid_gate())


def observations():
    return {
        "verified_resolution_delta": 0.0,
        "median_cost_ratio": 0.8,
    }


def evidence():
    return {
        "analysis": "analysis://frozen-result",
        "validity": "validity://review",
        "raw_run_completeness": "provenance://complete",
    }


class ValidationTests(unittest.TestCase):
    def test_valid_gate_has_no_issues(self):
        self.assertEqual(validate_promotion_gate(valid_gate()), ())

    def test_gate_requires_evidence_requirements(self):
        self.assertIn(
            "promotion gate requires explicit evidence requirements",
            validate_promotion_gate(valid_gate(required_evidence_keys=())),
        )

    def test_numeric_operator_requires_numeric_target(self):
        criterion = PromotionCriterion("x", "x", CriterionOperator.GTE, "high", "rationale")
        issues = validate_promotion_gate(valid_gate(criteria=(criterion,)))
        self.assertTrue(any("numeric operator requires numeric target" in issue for issue in issues))


class AssessmentTests(unittest.TestCase):
    def test_satisfied_gate_is_only_eligible_for_review(self):
        result = assess_promotion_gate(frozen_gate(), observations(), evidence())
        self.assertEqual(result.status, GateStatus.ELIGIBLE_FOR_REVIEW)
        self.assertNotIn('"PROMOTED"', result.to_json())

    def test_missing_observation_blocks(self):
        observed = observations()
        del observed["median_cost_ratio"]
        result = assess_promotion_gate(frozen_gate(), observed, evidence())
        self.assertEqual(result.status, GateStatus.BLOCKED)

    def test_missing_evidence_blocks(self):
        result = assess_promotion_gate(frozen_gate(), observations(), {"analysis": "analysis://x"})
        self.assertEqual(result.status, GateStatus.BLOCKED)

    def test_failed_criterion_is_not_eligible(self):
        result = assess_promotion_gate(
            frozen_gate(),
            {"verified_resolution_delta": -0.2, "median_cost_ratio": 0.8},
            evidence(),
        )
        self.assertEqual(result.status, GateStatus.NOT_ELIGIBLE)


class DecisionTests(unittest.TestCase):
    def test_non_finite_observation_blocks(self):
        for value in (float("inf"), float("-inf"), float("nan")):
            result = assess_promotion_gate(
                frozen_gate(),
                {"verified_resolution_delta": value, "median_cost_ratio": 0.8},
                evidence(),
            )
            self.assertEqual(result.status, GateStatus.BLOCKED)

    def test_decision_rejects_assessment_bound_to_other_gate(self):
        frozen = frozen_gate()
        eligible = assess_promotion_gate(frozen, observations(), evidence())
        forged = replace(eligible, gate_hash="sha256:" + "0" * 64)
        with self.assertRaises(ValueError):
            record_promotion_decision(
                forged,
                frozen_gate=frozen,
                observations=observations(),
                evidence=evidence(),
                promote=True,
                reviewer="reviewer",
                rationale="must not accept a mismatched gate binding",
                evidence_refs=("analysis://x",),
            )

    def test_decision_rejects_forged_eligible_status_even_with_correct_gate_hash(self):
        frozen = frozen_gate()
        blocked = assess_promotion_gate(frozen, {}, {})
        forged = replace(blocked, status=GateStatus.ELIGIBLE_FOR_REVIEW)
        with self.assertRaises(ValueError):
            record_promotion_decision(
                forged,
                frozen_gate=frozen,
                observations={},
                evidence={},
                promote=True,
                reviewer="reviewer",
                rationale="status declaration must not replace canonical evaluation",
                evidence_refs=("analysis://x",),
            )

    def test_decision_rejects_blank_evidence_reference(self):
        frozen = frozen_gate()
        eligible = assess_promotion_gate(frozen, observations(), evidence())
        with self.assertRaises(ValueError):
            record_promotion_decision(
                eligible,
                frozen_gate=frozen,
                observations=observations(),
                evidence=evidence(),
                promote=True,
                reviewer="reviewer",
                rationale="evidence must be substantive",
                evidence_refs=("   ",),
            )

    def test_promotion_requires_eligible_gate(self):
        blocked = assess_promotion_gate(frozen_gate(), {}, {})
        with self.assertRaises(ValueError):
            record_promotion_decision(
                blocked,
                frozen_gate=frozen_gate(),
                observations={},
                evidence={},
                promote=True,
                reviewer="reviewer",
                rationale="cannot override missing evidence",
                evidence_refs=("evidence://x",),
            )

    def test_eligible_still_requires_explicit_decision(self):
        eligible = assess_promotion_gate(frozen_gate(), observations(), evidence())
        record = record_promotion_decision(
            eligible,
            frozen_gate=frozen_gate(),
            observations=observations(),
            evidence=evidence(),
            promote=True,
            reviewer="reviewer",
            rationale="all frozen gates satisfied and evidence reviewed",
            evidence_refs=("analysis://frozen-result",),
        )
        self.assertEqual(record.decision, PromotionDecisionStatus.PROMOTED)

    def test_not_promoted_is_valid_even_when_eligible(self):
        eligible = assess_promotion_gate(frozen_gate(), observations(), evidence())
        record = record_promotion_decision(
            eligible,
            frozen_gate=frozen_gate(),
            observations=observations(),
            evidence=evidence(),
            promote=False,
            reviewer="reviewer",
            rationale="residual validity risk remains too high",
            evidence_refs=("validity://review",),
        )
        self.assertEqual(record.decision, PromotionDecisionStatus.NOT_PROMOTED)


class FreezeTests(unittest.TestCase):
    def test_gate_change_changes_hash(self):
        first = freeze_promotion_gate(valid_gate())
        changed = replace(valid_gate().criteria[0], target=0.0)
        second = freeze_promotion_gate(valid_gate(criteria=(changed, valid_gate().criteria[1])))
        self.assertNotEqual(first.content_hash, second.content_hash)


class FixtureTests(unittest.TestCase):
    def test_fixture_is_predeclared_gate_not_decision(self):
        path = Path(__file__).parents[1] / "experiments" / "promotion-gate-fixture.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        gate = PromotionGate.from_dict(payload["gate"])
        self.assertEqual(payload["fixture_type"], "PROMOTION_GATE_FIXTURE")
        self.assertEqual(validate_promotion_gate(gate), ())
        self.assertNotIn("decision", payload)


if __name__ == "__main__":
    unittest.main()
