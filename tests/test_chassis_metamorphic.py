import json
import unittest
from dataclasses import replace
from pathlib import Path

from arkx.characterization import TaskSignals, characterize
from arkx.progress import ProgressSnapshot, assess_progress
from arkx.promotion import PromotionGate, freeze_promotion_gate
from arkx.study import StudySpec, freeze_study_spec
from arkx.treatment import FallbackPolicy, TreatmentConfiguration, freeze_treatment_configuration
from arkx.workload import WorkloadManifest, freeze_workload_manifest


ROOT = Path(__file__).parents[1]
EXPERIMENTS = ROOT / "experiments"


def load_fixture(name: str, key: str) -> dict:
    return json.loads((EXPERIMENTS / name).read_text(encoding="utf-8"))[key]


class CharacterizationMetamorphicTests(unittest.TestCase):
    def test_order_and_duplicate_observation_noise_do_not_change_characterization(self):
        canonical = TaskSignals(
            candidate_files=("src/a.py", "src/b.py"),
            dependency_edges=(("src/a.py", "src/b.py"),),
            affected_components=("a",),
            known_tests=("test_a", "test_b"),
            ambiguity_markers=(),
            risk_markers=(),
            acceptance_checks=("tests pass",),
        )
        noisy = TaskSignals(
            candidate_files=("src/b.py", "src/a.py", "src/a.py"),
            dependency_edges=(("src/a.py", "src/b.py"), ("src/a.py", "src/b.py")),
            affected_components=("a", "a"),
            known_tests=("test_b", "test_a", "test_a"),
            ambiguity_markers=(),
            risk_markers=(),
            acceptance_checks=("tests pass", "tests pass"),
        )
        self.assertEqual(characterize(canonical).to_json(), characterize(noisy).to_json())


class ProgressMetamorphicTests(unittest.TestCase):
    def test_snapshot_order_and_duplicates_do_not_change_progress_assessment(self):
        previous = ProgressSnapshot(
            useful_files=("src/a.py", "src/b.py"),
            passing_tests=("test_old",),
            explained_failures=("known",),
            diff_distance=3,
            acceptance_distance=2,
            recent_actions=("inspect", "test"),
            failure_signatures=("failure-a",),
        )
        current = ProgressSnapshot(
            useful_files=("src/a.py", "src/b.py", "src/c.py"),
            passing_tests=("test_old", "test_new"),
            explained_failures=("known", "new"),
            diff_distance=2,
            acceptance_distance=1,
            recent_actions=("inspect", "test", "patch"),
            failure_signatures=(),
        )
        noisy_previous = replace(
            previous,
            useful_files=("src/b.py", "src/a.py", "src/a.py"),
            passing_tests=("test_old", "test_old"),
            recent_actions=("test", "inspect", "inspect"),
        )
        noisy_current = replace(
            current,
            useful_files=("src/c.py", "src/b.py", "src/a.py", "src/c.py"),
            passing_tests=("test_new", "test_old", "test_new"),
            explained_failures=("new", "known", "new"),
            recent_actions=("patch", "test", "inspect", "patch"),
        )
        self.assertEqual(
            assess_progress(previous, current).to_json(),
            assess_progress(noisy_previous, noisy_current).to_json(),
        )


class FrozenIdentityMetamorphicTests(unittest.TestCase):
    def test_study_set_like_fields_are_order_invariant(self):
        spec = StudySpec.from_dict(load_fixture("study-spec-fixture.json", "study_spec"))
        first = replace(
            spec,
            workload_refs=("workload://b", "workload://a"),
            treatment_refs=("config://b", "config://a"),
            metrics=("wall_time_ms", "verified_resolution", "monetary_cost"),
        )
        second = replace(
            first,
            workload_refs=tuple(reversed(first.workload_refs)),
            treatment_refs=tuple(reversed(first.treatment_refs)),
            metrics=tuple(reversed(first.metrics)),
        )
        self.assertEqual(
            freeze_study_spec(first).content_hash,
            freeze_study_spec(second).content_hash,
        )

    def test_treatment_mapping_and_fallback_order_are_invariant(self):
        config = TreatmentConfiguration.from_dict(
            load_fixture("treatment-configuration-fixture.json", "configuration")
        )
        first = replace(
            config,
            parameters={"temperature": 0, "max_tokens": 4096},
            fallback_policy=FallbackPolicy.FROZEN_EXPLICIT,
            fallback_targets=("config://b", "config://a"),
        )
        second = replace(
            first,
            parameters={"max_tokens": 4096, "temperature": 0},
            fallback_targets=("config://a", "config://b"),
        )
        self.assertEqual(
            freeze_treatment_configuration(first).content_hash,
            freeze_treatment_configuration(second).content_hash,
        )

    def test_promotion_gate_order_is_invariant(self):
        gate = PromotionGate.from_dict(load_fixture("promotion-gate-fixture.json", "gate"))
        reordered = replace(
            gate,
            criteria=tuple(reversed(gate.criteria)),
            required_evidence_keys=tuple(reversed(gate.required_evidence_keys)),
        )
        self.assertEqual(
            freeze_promotion_gate(gate).content_hash,
            freeze_promotion_gate(reordered).content_hash,
        )

    def test_fixed_workload_task_order_is_semantically_relevant(self):
        workload = WorkloadManifest.from_dict(
            load_fixture("workload-manifest-fixture.json", "workload")
        )
        reversed_tasks = replace(workload, task_refs=tuple(reversed(workload.task_refs)))
        self.assertNotEqual(
            freeze_workload_manifest(workload).content_hash,
            freeze_workload_manifest(reversed_tasks).content_hash,
        )

    def test_workload_criteria_order_is_not_semantically_relevant(self):
        workload = WorkloadManifest.from_dict(
            load_fixture("workload-manifest-fixture.json", "workload")
        )
        reordered = replace(
            workload,
            inclusion_criteria=tuple(reversed(workload.inclusion_criteria)),
            exclusion_criteria=tuple(reversed(workload.exclusion_criteria)),
        )
        self.assertEqual(
            freeze_workload_manifest(workload).content_hash,
            freeze_workload_manifest(reordered).content_hash,
        )


if __name__ == "__main__":
    unittest.main()
