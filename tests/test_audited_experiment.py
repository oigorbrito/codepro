import unittest
from types import SimpleNamespace

from arkx.harness import (
    AttemptSnapshot,
    ExperimentRecord,
    RunManifest,
    RunState,
    derive_experiment_identity_digest,
    validate_experiment_record_audited,
)


def attempt():
    manifest = RunManifest(
        experiment_id="exp", trial_id="trial", attempt_id="attempt", attempt_number=1,
        task_id="task", task_revision="rev", treatment="A", executor="executor",
        provider="provider", model="model", sandbox="sandbox", repository_revision="rev",
        configuration_digest="cfg", protocol_version="protocol", state=RunState.COMPLETED,
    )
    return AttemptSnapshot(manifest, {}, ())


class AuditedExperimentTests(unittest.TestCase):
    def test_experiment_requires_complete_audited_chain(self):
        record = ExperimentRecord(
            experiment_id="exp", protocol_version="protocol", input_manifest_digest="input",
            trial_ids=("trial",), attempt_ids=("attempt",), verification_refs=("verification://1",),
            acceptance_refs=("acceptance://1",), promotion_decision_ref="promotion://1",
            identity_digest=derive_experiment_identity_digest((attempt(),)),
            capability_digest="capabilities-1",
        )
        audit = SimpleNamespace(
            replay=SimpleNamespace(run_id="attempt"),
            integrity=SimpleNamespace(value="COMPLETE"),
            protocol_version="protocol",
            schema_version=1,
            configuration_digest="cfg",
            budget_digest=None,
            treatment="A",
            capability_digest="capabilities-1",
            chain=SimpleNamespace(to_dict=lambda: {
                "verification_ref": "verification://1", "acceptance_ref": "acceptance://1", "promotion_ref": "promotion://1",
            }),
        )
        validate_experiment_record_audited(record, (attempt(),), (audit,), promotion_attempt_id="attempt")

    def test_incomplete_audit_blocks_reproducible_experiment(self):
        record = ExperimentRecord(
            experiment_id="exp", protocol_version="protocol", input_manifest_digest="input",
            trial_ids=("trial",), attempt_ids=("attempt",), verification_refs=("verification://1",),
            identity_digest="wrong",
            capability_digest="capabilities-1",
        )
        audit = SimpleNamespace(
            replay=SimpleNamespace(run_id="attempt"),
            integrity=SimpleNamespace(value="INCOMPLETE"),
            protocol_version="protocol",
            schema_version=1,
            configuration_digest="cfg",
            budget_digest=None,
            treatment="A",
            capability_digest="capabilities-1",
            chain=SimpleNamespace(to_dict=lambda: {"verification_ref": "verification://1"}),
        )
        with self.assertRaises(ValueError):
            validate_experiment_record_audited(record, (attempt(),), (audit,))


if __name__ == "__main__":
    unittest.main()
