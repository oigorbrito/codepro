import json
import unittest
from dataclasses import replace
from pathlib import Path

from arkx.environment import (
    ActionPin,
    EnvironmentManifest,
    freeze_environment_manifest,
    validate_environment_manifest,
)


def valid(**overrides):
    values = {
        "environment_id": "arkx-ci-python-3.14.7-ubuntu-24.04",
        "operating_system": "Ubuntu",
        "operating_system_version": "24.04",
        "runner_image": "ubuntu-24.04",
        "runner_image_version": "record-at-run-time",
        "architecture": "x86_64",
        "python_implementation": "CPython",
        "python_version": "3.14.7",
        "locale": "C.UTF-8",
        "timezone": "UTC",
        "dependency_lock_ref": None,
        "dependency_lock_hash": None,
        "dependency_lock_justification": "current chassis uses Python standard library only",
        "container_image_digest": None,
        "non_container_justification": "foundation CI uses a GitHub-hosted runner and records its image version per run",
        "action_pins": (
            ActionPin("actions/checkout", "11d5960a326750d5838078e36cf38b85af677262"),
            ActionPin("actions/setup-python", "a26af69be951a213d495a4c3e4e4022e16d87065"),
        ),
        "hermetic": False,
        "nonhermetic_reasons": (
            "GitHub-hosted ubuntu-24.04 image is versioned at run time but not selected by immutable image digest",
        ),
        "network_policy": "network is not required by foundation tests",
    }
    values.update(overrides)
    return EnvironmentManifest(**values)


class ValidationTests(unittest.TestCase):
    def test_valid_environment_has_no_issues(self):
        self.assertEqual(validate_environment_manifest(valid()), ())

    def test_action_pin_must_be_full_sha(self):
        env = valid(action_pins=(ActionPin("actions/checkout", "v4"),))
        self.assertIn("action pins must use full 40-character commit SHAs", validate_environment_manifest(env))

    def test_no_dependency_lock_requires_justification(self):
        issues = validate_environment_manifest(valid(dependency_lock_justification=None))
        self.assertIn("missing dependency lock requires explicit justification", issues)

    def test_nonhermetic_environment_must_state_residual_drift(self):
        issues = validate_environment_manifest(valid(nonhermetic_reasons=()))
        self.assertIn("non-hermetic environment must declare residual drift reasons", issues)

    def test_hermetic_cannot_claim_known_drift(self):
        issues = validate_environment_manifest(valid(hermetic=True))
        self.assertIn("hermetic environment cannot declare nonhermetic_reasons", issues)


class ParsingTests(unittest.TestCase):
    def test_string_false_is_not_coerced_to_true(self):
        payload = valid().to_dict()
        payload["hermetic"] = "false"
        with self.assertRaises(ValueError):
            EnvironmentManifest.from_dict(payload)

    def test_string_schema_version_is_rejected(self):
        payload = valid().to_dict()
        payload["schema_version"] = "1"
        with self.assertRaises(ValueError):
            EnvironmentManifest.from_dict(payload)

    def test_non_collection_action_pins_are_rejected(self):
        payload = valid().to_dict()
        payload["action_pins"] = "actions/checkout"
        with self.assertRaises(ValueError):
            EnvironmentManifest.from_dict(payload)


class FreezeTests(unittest.TestCase):
    def test_same_environment_has_same_hash(self):
        self.assertEqual(
            freeze_environment_manifest(valid()).to_json(),
            freeze_environment_manifest(valid()).to_json(),
        )

    def test_image_version_change_changes_hash(self):
        first = freeze_environment_manifest(valid())
        second = freeze_environment_manifest(replace(valid(), runner_image_version="different"))
        self.assertNotEqual(first.content_hash, second.content_hash)

    def test_invalid_environment_cannot_be_frozen(self):
        with self.assertRaises(ValueError):
            freeze_environment_manifest(valid(action_pins=()))


class FixtureTests(unittest.TestCase):
    def test_fixture_discloses_nonhermetic_runner(self):
        path = Path(__file__).parents[1] / "experiments" / "environment-manifest-fixture.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        env = EnvironmentManifest.from_dict(value["environment"])
        self.assertEqual(value["fixture_type"], "ENVIRONMENT_MANIFEST_FIXTURE")
        self.assertFalse(env.hermetic)
        self.assertEqual(validate_environment_manifest(env), ())


if __name__ == "__main__":
    unittest.main()
