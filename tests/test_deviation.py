import json
import unittest
from dataclasses import replace
from pathlib import Path

from arkx.deviation import (
    AnalysisImpact,
    DeviationPhase,
    DeviationType,
    ProtocolDeviation,
    freeze_protocol_deviation,
    validate_protocol_deviation,
)


def valid(**overrides):
    values = {
        "deviation_id": "dev-001",
        "study_spec_ref": "git:frozen-study",
        "scope_ref": "run://001",
        "deviation_type": DeviationType.MODEL_OR_PROVIDER_SWITCH,
        "phase": DeviationPhase.DURING_EXECUTION,
        "frozen_value": "provider-a/model-a",
        "observed_value": "provider-b/model-b",
        "reason": "provider-a unavailable",
        "evidence_refs": ("raw://provider-a-unavailable.json",),
        "preauthorized_by_frozen_protocol": False,
        "analysis_impact": AnalysisImpact.REQUIRES_NEW_STUDY,
        "impact_rationale": "treatment identity changed",
        "replacement_study_spec_ref": "git:new-frozen-study",
    }
    values.update(overrides)
    return ProtocolDeviation(**values)


class ValidationTests(unittest.TestCase):
    def test_valid_deviation_has_no_issues(self):
        self.assertEqual(validate_protocol_deviation(valid()), ())

    def test_before_and_after_must_differ(self):
        issues = validate_protocol_deviation(valid(observed_value="provider-a/model-a"))
        self.assertIn("deviation must record an actual before/after difference", issues)

    def test_unplanned_switch_cannot_claim_no_effect(self):
        issues = validate_protocol_deviation(
            valid(
                analysis_impact=AnalysisImpact.NO_PRIMARY_EFFECT,
                replacement_study_spec_ref=None,
            )
        )
        self.assertIn(
            "unplanned behavior-affecting deviation cannot claim NO_PRIMARY_EFFECT without frozen preauthorization",
            issues,
        )

    def test_new_study_impact_requires_new_spec_ref(self):
        issues = validate_protocol_deviation(valid(replacement_study_spec_ref=None))
        self.assertIn("REQUIRES_NEW_STUDY requires replacement_study_spec_ref", issues)

    def test_deviation_requires_evidence(self):
        self.assertIn(
            "protocol deviation requires at least one evidence reference",
            validate_protocol_deviation(valid(evidence_refs=())),
        )


class FreezeTests(unittest.TestCase):
    def test_same_deviation_has_same_hash(self):
        self.assertEqual(
            freeze_protocol_deviation(valid()).to_json(),
            freeze_protocol_deviation(valid()).to_json(),
        )

    def test_changed_observed_value_changes_hash(self):
        first = freeze_protocol_deviation(valid())
        second = freeze_protocol_deviation(replace(valid(), observed_value="provider-c/model-c"))
        self.assertNotEqual(first.content_hash, second.content_hash)


class FixtureTests(unittest.TestCase):
    def test_fixture_forbids_silent_provider_switch(self):
        path = Path(__file__).parents[1] / "experiments" / "protocol-deviation-fixture.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        value = ProtocolDeviation.from_dict(payload["deviation"])
        self.assertEqual(payload["fixture_type"], "PROTOCOL_DEVIATION_FIXTURE")
        self.assertEqual(value.analysis_impact, AnalysisImpact.REQUIRES_NEW_STUDY)
        self.assertEqual(validate_protocol_deviation(value), ())


if __name__ == "__main__":
    unittest.main()
