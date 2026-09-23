import json
import unittest
from dataclasses import replace
from pathlib import Path

from arkx.provenance import (
    RunManifest,
    freeze_run_manifest,
    hash_execution_record,
    validate_run_manifest,
)


def valid(**overrides):
    values = {
        "run_id": "run-001",
        "study_spec_hash": "sha256:" + "a" * 64,
        "study_spec_ref": "git:47da1e44e2fb3830c344d98c13dcb03a2f24eba8:experiments/study.json",
        "arkx_commit": "998438c2c29fa21014823966c1273fc827e3089d",
        "task_ref": "benchmark://swebench/verified/task-001",
        "configuration_ref": "config://bounded-routing-v1",
        "repetition_index": 1,
        "executor_id": "executor",
        "executor_version": "1.0.0",
        "environment_ref": "env://arkx-ci-python-3.14.7-ubuntu-24.04",
        "execution_record_ref": "raw://runs/run-001.json",
        "execution_record_hash": "sha256:" + "b" * 64,
        "protocol_deviations": (),
    }
    values.update(overrides)
    return RunManifest(**values)


class ValidationTests(unittest.TestCase):
    def test_valid_manifest_has_no_issues(self):
        self.assertEqual(validate_run_manifest(valid()), ())

    def test_missing_study_ref_fails_closed(self):
        self.assertIn("study_spec_ref must be non-empty", validate_run_manifest(valid(study_spec_ref="")))

    def test_short_commit_is_rejected(self):
        self.assertIn("arkx_commit must be a full 40-character git SHA", validate_run_manifest(valid(arkx_commit="abc")))

    def test_raw_record_hash_is_required_in_canonical_form(self):
        self.assertIn("execution_record_hash must be a canonical sha256 reference", validate_run_manifest(valid(execution_record_hash="unknown")))

    def test_repetition_index_is_one_based(self):
        self.assertIn("repetition_index must be at least 1", validate_run_manifest(valid(repetition_index=0)))


class IntegrityTests(unittest.TestCase):
    def test_same_manifest_has_same_hash(self):
        self.assertEqual(freeze_run_manifest(valid()).to_json(), freeze_run_manifest(valid()).to_json())

    def test_provenance_change_changes_hash(self):
        first = freeze_run_manifest(valid())
        second = freeze_run_manifest(replace(valid(), configuration_ref="config://direct-v1"))
        self.assertNotEqual(first.content_hash, second.content_hash)

    def test_invalid_manifest_cannot_be_frozen(self):
        with self.assertRaises(ValueError):
            freeze_run_manifest(valid(arkx_commit="mutable-branch"))

    def test_execution_record_hash_is_byte_sensitive(self):
        self.assertNotEqual(hash_execution_record('{"a":1}'), hash_execution_record('{"a": 1}'))

    def test_round_trip_preserves_semantics(self):
        manifest = valid()
        self.assertEqual(RunManifest.from_json(manifest.to_json()).to_dict(), manifest.to_dict())


class FixtureTests(unittest.TestCase):
    def test_fixture_binds_one_raw_run_to_design_and_environment(self):
        path = Path(__file__).parents[1] / "experiments" / "run-manifest-fixture.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(value["fixture_type"], "RUN_MANIFEST_FIXTURE")
        manifest = RunManifest.from_dict(value["run_manifest"])
        self.assertEqual(validate_run_manifest(manifest), ())
        self.assertNotEqual(freeze_run_manifest(manifest).content_hash, manifest.execution_record_hash)


if __name__ == "__main__":
    unittest.main()
