import json
import unittest
from dataclasses import replace
from pathlib import Path

from arkx.treatment import (
    FallbackPolicy,
    SeedSupport,
    TreatmentConfiguration,
    freeze_treatment_configuration,
    validate_treatment_configuration,
)


def digest(char):
    return "sha256:" + char * 64


def valid(**overrides):
    values = {
        "configuration_id": "openrouter-mini-v1",
        "executor_id": "mini-swe-agent-adapter",
        "executor_version": "pinned-revision-v1",
        "provider_id": "openrouter",
        "model_id": "provider/model",
        "model_revision": None,
        "model_revision_justification": "provider exposes a stable model identifier but no immutable serving-weight revision",
        "prompt_ref": "prompt://repair-v1",
        "prompt_hash": digest("a"),
        "tool_surface_ref": "tools://bash-edit-test-v1",
        "tool_surface_hash": digest("b"),
        "provider_routing_ref": "routing://single-provider-no-silent-switch-v1",
        "parameters": {"temperature": 0, "max_tokens": 4096},
        "max_attempts": 3,
        "timeout_seconds": 600,
        "fallback_policy": FallbackPolicy.DISABLED,
        "fallback_targets": (),
        "seed_support": SeedSupport.UNSUPPORTED,
        "seed": None,
        "seed_justification": "provider endpoint does not guarantee deterministic seeding",
    }
    values.update(overrides)
    return TreatmentConfiguration(**values)


class ValidationTests(unittest.TestCase):
    def test_valid_configuration_has_no_issues(self):
        self.assertEqual(validate_treatment_configuration(valid()), ())

    def test_prompt_hash_is_required_in_canonical_form(self):
        self.assertIn(
            "prompt_hash must be a canonical sha256 reference",
            validate_treatment_configuration(valid(prompt_hash="mutable")),
        )

    def test_provider_and_model_are_atomic_identity(self):
        issues = validate_treatment_configuration(valid(model_id=None))
        self.assertIn("provider_id and model_id must either both be declared or both be absent", issues)

    def test_missing_model_revision_requires_disclosure(self):
        issues = validate_treatment_configuration(valid(model_revision_justification=None))
        self.assertIn("missing model revision requires explicit justification", issues)

    def test_silent_fallback_shape_is_rejected(self):
        issues = validate_treatment_configuration(valid(fallback_targets=("config://other",)))
        self.assertIn("DISABLED fallback policy cannot declare fallback_targets", issues)

    def test_explicit_fallback_requires_targets(self):
        issues = validate_treatment_configuration(
            valid(fallback_policy=FallbackPolicy.FROZEN_EXPLICIT, fallback_targets=())
        )
        self.assertIn("FROZEN_EXPLICIT fallback policy requires frozen fallback_targets", issues)

    def test_unsupported_seed_requires_disclosure(self):
        issues = validate_treatment_configuration(valid(seed_justification=None))
        self.assertIn("unsupported/not-applicable seed policy requires justification", issues)


class FreezeTests(unittest.TestCase):
    def test_same_configuration_has_same_hash(self):
        self.assertEqual(
            freeze_treatment_configuration(valid()).to_json(),
            freeze_treatment_configuration(valid()).to_json(),
        )

    def test_prompt_change_changes_identity(self):
        first = freeze_treatment_configuration(valid())
        second = freeze_treatment_configuration(replace(valid(), prompt_hash=digest("c")))
        self.assertNotEqual(first.content_hash, second.content_hash)

    def test_model_change_changes_identity(self):
        first = freeze_treatment_configuration(valid())
        second = freeze_treatment_configuration(replace(valid(), model_id="provider/other-model"))
        self.assertNotEqual(first.content_hash, second.content_hash)


class FixtureTests(unittest.TestCase):
    def test_fixture_discloses_provider_revision_and_seed_limits(self):
        path = Path(__file__).parents[1] / "experiments" / "treatment-configuration-fixture.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        config = TreatmentConfiguration.from_dict(value["configuration"])
        self.assertEqual(value["fixture_type"], "TREATMENT_CONFIGURATION_FIXTURE")
        self.assertEqual(validate_treatment_configuration(config), ())
        self.assertIsNone(config.model_revision)
        self.assertEqual(config.seed_support, SeedSupport.UNSUPPORTED)


if __name__ == "__main__":
    unittest.main()
