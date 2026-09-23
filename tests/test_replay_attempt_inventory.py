import unittest
from pathlib import Path

from arkx.event_log import ReplayChain, classify_snapshot_chain_references
from arkx.harness import AttemptSnapshot, RunManifest, RunState, derive_attempt_id


class ReplayAttemptInventoryTests(unittest.TestCase):
    def test_snapshot_inventory_classifies_physical_and_missing_refs(self):
        trial_id = "trial-task-treatment-1"
        manifest = RunManifest(
            experiment_id="exp-1", trial_id=trial_id,
            attempt_id=derive_attempt_id(trial_id=trial_id, attempt_number=1, configuration_digest="cfg-a"),
            attempt_number=1, task_id="task-1", task_revision="rev", treatment="A",
            executor="executor", provider="provider", model="model", sandbox="sandbox",
            repository_revision="repo", configuration_digest="cfg-a", protocol_version="p1",
            state=RunState.BLOCKED, artifact_refs=("artifact://manifest",),
        )
        snapshot = AttemptSnapshot(manifest, {}, (Path("D:/artifacts/execution.json"),))
        physical_ref = str(Path("D:/artifacts/execution.json"))
        report = classify_snapshot_chain_references(snapshot, ReplayChain(execution_ref=physical_ref, verification_ref="missing://verification"))
        self.assertEqual(report.status(), "MISSING")
        self.assertIn(physical_ref, report.present)
        self.assertIn("missing://verification", report.missing)


if __name__ == "__main__":
    unittest.main()
