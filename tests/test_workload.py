import json
import unittest
from dataclasses import replace
from pathlib import Path

from arkx.workload import (
    SamplingStrategy,
    TaskOrderPolicy,
    WorkloadManifest,
    freeze_workload_manifest,
    validate_workload_manifest,
)


def valid(**overrides):
    values = {
        "workload_id": "swebench-verified-wave0",
        "source_ref": "benchmark://swebench-verified",
        "source_version": "pinned-revision-v1",
        "target_population": "repository-level software repair tasks represented by SWE-bench Verified",
        "sampling_strategy": SamplingStrategy.FIXED_SAMPLE,
        "selection_rule": "use the frozen verifier-qualified Wave 0 task list",
        "selection_justification": "qualification is frozen before treatment and applies equally to all configurations",
        "inclusion_criteria": ("verifier executable", "repository materializable"),
        "exclusion_criteria": ("known corrupted task",),
        "task_refs": ("task://one", "task://two"),
        "holdout_policy": "no treatment-specific task replacement; holdout membership remains frozen",
        "task_order_policy": TaskOrderPolicy.FIXED,
        "random_seed": None,
    }
    values.update(overrides)
    return WorkloadManifest(**values)


class ValidationTests(unittest.TestCase):
    def test_valid_workload_has_no_issues(self):
        self.assertEqual(validate_workload_manifest(valid()), ())

    def test_empty_workload_fails_closed(self):
        self.assertIn("task_refs must contain at least one frozen task", validate_workload_manifest(valid(task_refs=())))

    def test_duplicate_tasks_are_rejected(self):
        self.assertIn("task_refs must not contain duplicates", validate_workload_manifest(valid(task_refs=("task://one", "task://one"))))

    def test_randomized_order_requires_seed(self):
        self.assertIn(
            "RANDOMIZED task order requires random_seed",
            validate_workload_manifest(valid(task_order_policy=TaskOrderPolicy.RANDOMIZED)),
        )

    def test_random_sample_requires_seed(self):
        self.assertIn(
            "RANDOM_SAMPLE requires random_seed",
            validate_workload_manifest(valid(sampling_strategy=SamplingStrategy.RANDOM_SAMPLE)),
        )

    def test_criteria_cannot_contradict(self):
        issues = validate_workload_manifest(
            valid(inclusion_criteria=("same",), exclusion_criteria=("same",))
        )
        self.assertIn("the same criterion cannot be both inclusion and exclusion", issues)


class FreezeTests(unittest.TestCase):
    def test_same_workload_has_same_hash(self):
        self.assertEqual(
            freeze_workload_manifest(valid()).to_json(),
            freeze_workload_manifest(valid()).to_json(),
        )

    def test_task_change_changes_hash(self):
        first = freeze_workload_manifest(valid())
        second = freeze_workload_manifest(replace(valid(), task_refs=("task://one", "task://three")))
        self.assertNotEqual(first.content_hash, second.content_hash)

    def test_invalid_workload_cannot_be_frozen(self):
        with self.assertRaises(ValueError):
            freeze_workload_manifest(valid(task_refs=()))


class FixtureTests(unittest.TestCase):
    def test_fixture_contains_frozen_selection_semantics(self):
        path = Path(__file__).parents[1] / "experiments" / "workload-manifest-fixture.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        workload = WorkloadManifest.from_dict(value["workload"])
        self.assertEqual(value["fixture_type"], "WORKLOAD_MANIFEST_FIXTURE")
        self.assertEqual(validate_workload_manifest(workload), ())


if __name__ == "__main__":
    unittest.main()
