import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from arkx.harness import (
    ArtifactStore,
    ArtifactRecord,
    ArtifactStatus,
    ErrorDomain,
    ErrorEnvelope,
    LifecycleEvent,
    Retryability,
    RecoveryLineage,
    RetryLineage,
    RunManifest,
    RunState,
    derive_attempt_id,
    validate_execution_artifact_consistency,
    load_attempt,
    AcceptanceEvidence,
    VerificationEvidence,
    ExperimentRecord,
    load_experiment_record,
    write_experiment_record,
    AttemptStore,
    ComparabilityStatus,
    compare_attempts,
    compare_attempt_collection,
    evidence_from_snapshot,
    validate_transition,
)


class HarnessContractTests(unittest.TestCase):
    def manifest(self, **changes):
        values = {
            "experiment_id": "exp-1",
            "trial_id": "trial-task-treatment-1",
            "attempt_id": derive_attempt_id(
                trial_id="trial-task-treatment-1",
                attempt_number=1,
                configuration_digest="cfg-a",
            ),
            "attempt_number": 1,
            "task_id": "task-1",
            "task_revision": "task-rev-1",
            "treatment": "A",
            "executor": "executor-x",
            "provider": "provider-x",
            "model": "model-x",
            "sandbox": "sandbox-x",
            "repository_revision": "repo-rev-1",
            "configuration_digest": "cfg-a",
            "protocol_version": "protocol-1",
        }
        values.update(changes)
        return RunManifest(**values)

    def test_manifest_has_distinct_trial_and_attempt_identity(self):
        first = self.manifest()
        second = self.manifest(
            attempt_number=2,
            attempt_id=derive_attempt_id(
                trial_id=first.trial_id,
                attempt_number=2,
                configuration_digest=first.configuration_digest,
            ),
        )
        self.assertNotEqual(first.trial_id, first.attempt_id)
        self.assertNotEqual(first.attempt_id, second.attempt_id)

    def test_attempt_identity_is_stable_and_configuration_sensitive(self):
        first = derive_attempt_id(trial_id="t", attempt_number=1, configuration_digest="a")
        self.assertEqual(first, derive_attempt_id(trial_id="t", attempt_number=1, configuration_digest="a"))
        self.assertNotEqual(first, derive_attempt_id(trial_id="t", attempt_number=1, configuration_digest="b"))

    def test_error_taxonomy_preserves_retryability_and_raw_evidence(self):
        error = ErrorEnvelope(
            domain=ErrorDomain.PROVIDER,
            code="PROVIDER_OVERLOADED",
            message="temporary overload",
            retryability=Retryability.RETRYABLE,
            raw_evidence_refs=("raw-b", "raw-a", "raw-a"),
            attempt_number=2,
        )
        self.assertEqual(error.to_dict()["raw_evidence_refs"], ["raw-a", "raw-b"])
        self.assertEqual(error.to_dict()["retryability"], "RETRYABLE")

    def test_manifest_serialization_is_deterministic(self):
        first = self.manifest(
            state=RunState.BLOCKED,
            artifact_refs=("z", "a", "a"),
            errors=(ErrorEnvelope(ErrorDomain.SANDBOX, "SANDBOX_UNAVAILABLE", "daemon unavailable"),),
        )
        second = self.manifest(
            state=RunState.BLOCKED,
            artifact_refs=("a", "z"),
            errors=(ErrorEnvelope(ErrorDomain.SANDBOX, "SANDBOX_UNAVAILABLE", "daemon unavailable"),),
        )
        self.assertEqual(first.to_json(), second.to_json())

    def test_manifest_round_trip_supports_replay_validation(self):
        original = self.manifest(state=RunState.BLOCKED)
        restored = RunManifest.from_json(original.to_json())
        restored.validate_attempt_identity()
        self.assertEqual(restored.to_json(), original.to_json())

    def test_replay_validation_rejects_identity_drift(self):
        original = self.manifest()
        drifted = self.manifest(attempt_id="different-attempt")
        with self.assertRaises(ValueError):
            drifted.validate_attempt_identity()

    def test_lifecycle_validation_requires_error_for_blocked(self):
        blocked = self.manifest(state=RunState.BLOCKED)
        with self.assertRaises(ValueError):
            blocked.validate_lifecycle()
        valid = self.manifest(
            state=RunState.BLOCKED,
            errors=(ErrorEnvelope(ErrorDomain.SANDBOX, "SANDBOX_UNAVAILABLE", "daemon unavailable"),),
        )
        valid.validate_lifecycle()

    def test_lifecycle_validation_rejects_completed_with_error(self):
        completed = self.manifest(
            state=RunState.COMPLETED,
            errors=(ErrorEnvelope(ErrorDomain.EXECUTOR, "EXECUTOR_FAILED", "failed"),),
        )
        with self.assertRaises(ValueError):
            completed.validate_lifecycle()

    def test_lifecycle_transitions_are_explicit(self):
        validate_transition(RunState.PLANNED, RunState.STARTED)
        validate_transition(RunState.STARTED, RunState.EXECUTING)
        validate_transition(RunState.EXECUTING, RunState.BLOCKED)
        with self.assertRaises(ValueError):
            validate_transition(RunState.PLANNED, RunState.COMPLETED)
        with self.assertRaises(ValueError):
            validate_transition(RunState.COMPLETED, RunState.EXECUTING)

    def test_state_history_is_validated(self):
        valid = self.manifest(
            state=RunState.COMPLETED,
            state_history=(RunState.PLANNED, RunState.STARTED, RunState.EXECUTING, RunState.COMPLETED),
        )
        valid.validate_lifecycle()
        invalid = self.manifest(
            state=RunState.COMPLETED,
            state_history=(RunState.PLANNED, RunState.COMPLETED),
        )
        with self.assertRaises(ValueError):
            invalid.validate_lifecycle()

    def test_lifecycle_events_match_history_and_are_monotonic(self):
        events = (
            LifecycleEvent(RunState.PLANNED, "2026-01-01T00:00:00+00:00"),
            LifecycleEvent(RunState.STARTED, "2026-01-01T00:00:01+00:00"),
        )
        manifest = self.manifest(state=RunState.STARTED, state_history=(RunState.PLANNED, RunState.STARTED), lifecycle_events=events)
        manifest.validate_lifecycle()
        invalid = self.manifest(state=RunState.STARTED, state_history=(RunState.PLANNED, RunState.STARTED), lifecycle_events=tuple(reversed(events)))
        with self.assertRaises(ValueError):
            invalid.validate_lifecycle()

    def test_missing_identity_is_preserved_for_blocked_runs(self):
        manifest = self.manifest(provider=None, state=RunState.BLOCKED)
        self.assertIsNone(manifest.to_dict()["provider"])
        self.assertEqual(manifest.to_dict()["state"], "BLOCKED")

    def test_invalid_attempt_number_is_rejected(self):
        with self.assertRaises(ValueError):
            derive_attempt_id(trial_id="t", attempt_number=0, configuration_digest="cfg")

    def test_artifact_store_reserves_once_and_writes_atomically(self):
        with TemporaryDirectory() as directory:
            store = ArtifactStore(directory)
            attempt = store.reserve_attempt("task-1", 1)
            target = store.write_text_atomic(attempt / "execution.json", "{}\n")
            self.assertEqual(Path(target).read_text(encoding="utf-8"), "{}\n")
            with self.assertRaises(FileExistsError):
                store.reserve_attempt("task-1", 1)

    def test_artifact_store_rejects_path_escape(self):
        with TemporaryDirectory() as directory:
            store = ArtifactStore(directory)
            with self.assertRaises(ValueError):
                store.reserve_attempt("../escape", 1)

    def test_artifact_store_reserves_retry_and_persists_lineage(self):
        with TemporaryDirectory() as directory:
            store = ArtifactStore(directory)
            previous = derive_attempt_id(trial_id="trial", attempt_number=1, configuration_digest="cfg")
            path = store.reserve_retry_attempt("task-1", trial_id="trial", previous_attempt_id=previous, previous_attempt_number=1, configuration_digest="cfg")
            lineage = json.loads((path / "retry-lineage.json").read_text(encoding="utf-8"))
            self.assertEqual(lineage["previous_attempt_id"], previous)
            self.assertEqual(lineage["attempt_number"], 2)
            with self.assertRaises(FileExistsError):
                store.reserve_retry_attempt("task-1", trial_id="trial", previous_attempt_id=previous, previous_attempt_number=1, configuration_digest="cfg")

    def test_artifact_store_rejects_retry_identity_drift(self):
        with TemporaryDirectory() as directory:
            store = ArtifactStore(directory)
            with self.assertRaises(ValueError):
                store.reserve_retry_attempt("task-1", trial_id="trial", previous_attempt_id="wrong", previous_attempt_number=1, configuration_digest="cfg")

    def test_artifact_store_reserves_recovery_attempt_with_causal_lineage(self):
        with TemporaryDirectory() as directory:
            store = ArtifactStore(directory)
            source = derive_attempt_id(trial_id="trial", attempt_number=1, configuration_digest="cfg")
            path = store.reserve_recovery_attempt("task-1", trial_id="trial", source_attempt_id=source, source_attempt_number=1, configuration_digest="cfg", recovery_reference="recovery://1")
            lineage = json.loads((path / "recovery-lineage.json").read_text(encoding="utf-8"))
            self.assertEqual(lineage["source_attempt_id"], source)
            self.assertNotEqual(lineage["attempt_id"], source)
            with self.assertRaises(FileExistsError):
                store.reserve_recovery_attempt("task-1", trial_id="trial", source_attempt_id=source, source_attempt_number=1, configuration_digest="cfg", recovery_reference="recovery://1")

    def test_retry_lineage_round_trips_and_validates_manifest_link(self):
        lineage = RetryLineage.from_dict({
            "trial_id": "trial", "previous_attempt_id": derive_attempt_id(trial_id="trial", attempt_number=1, configuration_digest="cfg"),
            "previous_attempt_number": 1, "attempt_id": derive_attempt_id(trial_id="trial", attempt_number=2, configuration_digest="cfg"),
            "attempt_number": 2, "configuration_digest": "cfg",
        })
        self.assertEqual(RetryLineage.from_dict(lineage.to_dict()), lineage)
        with self.assertRaises(ValueError):
            RetryLineage.from_dict({**lineage.to_dict(), "attempt_id": "wrong"})

    def test_recovery_lineage_round_trips_and_validates_identity(self):
        lineage = RecoveryLineage.from_dict({
            "trial_id": "trial", "source_attempt_id": derive_attempt_id(trial_id="trial", attempt_number=1, configuration_digest="cfg"),
            "source_attempt_number": 1, "attempt_id": derive_attempt_id(trial_id="trial", attempt_number=2, configuration_digest="cfg"),
            "attempt_number": 2, "configuration_digest": "cfg", "recovery_reference": "recovery://1",
        })
        self.assertEqual(RecoveryLineage.from_dict(lineage.to_dict()), lineage)
        with self.assertRaises(ValueError):
            RecoveryLineage.from_dict({**lineage.to_dict(), "source_attempt_id": "wrong"})

    def test_manifest_binds_budget_ledger_to_attempt_and_digest(self):
        manifest = self.manifest(budget_digest="budget-digest")
        ledger = {"budget_digest": "budget-digest", "consumed_attempts": [manifest.attempt_id], "tokens_used": 2}
        bound = manifest.with_budget_ledger(ledger)
        self.assertEqual(bound.budget_ledger["consumed_attempts"], [manifest.attempt_id])
        with self.assertRaises(ValueError):
            manifest.with_budget_ledger({"budget_digest": "other", "consumed_attempts": [manifest.attempt_id]})

    def test_artifact_store_writes_bound_manifest_atomically(self):
        with TemporaryDirectory() as directory:
            store = ArtifactStore(directory)
            attempt_root = store.reserve_attempt("task-1", 1)
            manifest = self.manifest(budget_digest="budget-digest")
            bound = manifest.with_budget_ledger({"budget_digest": "budget-digest", "consumed_attempts": [manifest.attempt_id]})
            target = store.write_manifest(attempt_root, bound)
            loaded = RunManifest.from_json(Path(target).read_text(encoding="utf-8"))
            self.assertEqual(loaded.budget_ledger["budget_digest"], "budget-digest")

    def test_artifact_store_manifest_must_match_recovery_lineage(self):
        with TemporaryDirectory() as directory:
            store = ArtifactStore(directory)
            source = derive_attempt_id(trial_id="trial", attempt_number=1, configuration_digest="cfg")
            attempt_root = store.reserve_recovery_attempt("task-1", trial_id="trial", source_attempt_id=source, source_attempt_number=1, configuration_digest="cfg", recovery_reference="recovery://1")
            with self.assertRaises(ValueError):
                store.write_manifest(attempt_root, self.manifest(attempt_id="wrong", trial_id="trial", configuration_digest="cfg"))

    def test_artifact_store_recovery_respects_persisted_budget_ledger(self):
        with TemporaryDirectory() as directory:
            store = ArtifactStore(directory)
            source = derive_attempt_id(trial_id="trial", attempt_number=1, configuration_digest="cfg")
            ledger = {"consumed_attempts": [source], "budget": {"max_attempts": 1}}
            with self.assertRaises(ValueError):
                store.reserve_recovery_attempt("task-1", trial_id="trial", source_attempt_id=source, source_attempt_number=1, configuration_digest="cfg", recovery_reference="recovery://1", budget_ledger=ledger)
            self.assertFalse((Path(directory) / "task-1" / "attempt-2").exists())

    def test_artifact_store_retry_respects_persisted_budget_ledger(self):
        with TemporaryDirectory() as directory:
            store = ArtifactStore(directory)
            source = derive_attempt_id(trial_id="trial", attempt_number=1, configuration_digest="cfg")
            ledger = {"consumed_attempts": [source], "budget": {"max_attempts": 1}}
            with self.assertRaises(ValueError):
                store.reserve_retry_attempt("task-1", trial_id="trial", previous_attempt_id=source, previous_attempt_number=1, configuration_digest="cfg", budget_ledger=ledger)
            self.assertFalse((Path(directory) / "task-1" / "attempt-2").exists())

    def test_artifact_store_persists_updated_budget_ledger_for_retry(self):
        with TemporaryDirectory() as directory:
            store = ArtifactStore(directory)
            source = derive_attempt_id(trial_id="trial", attempt_number=1, configuration_digest="cfg")
            ledger = {"consumed_attempts": [source], "budget": {"max_attempts": 2}}
            path = store.reserve_retry_attempt("task-1", trial_id="trial", previous_attempt_id=source, previous_attempt_number=1, configuration_digest="cfg", budget_ledger=ledger)
            persisted = json.loads((path / "budget-ledger.json").read_text(encoding="utf-8"))
            self.assertEqual(len(persisted["consumed_attempts"]), 2)
            self.assertNotEqual(persisted, ledger)

    def test_manifest_must_match_persisted_budget_ledger(self):
        with TemporaryDirectory() as directory:
            store = ArtifactStore(directory)
            source = derive_attempt_id(trial_id="trial", attempt_number=1, configuration_digest="cfg")
            ledger = {"consumed_attempts": [source], "budget": {"max_attempts": 2}}
            path = store.reserve_retry_attempt("task-1", trial_id="trial", previous_attempt_id=source, previous_attempt_number=1, configuration_digest="cfg", budget_ledger=ledger)
            attempt_id = derive_attempt_id(trial_id="trial", attempt_number=2, configuration_digest="cfg")
            manifest = self.manifest(trial_id="trial", attempt_id=attempt_id, attempt_number=2, configuration_digest="cfg", budget_ledger=ledger)
            with self.assertRaises(ValueError):
                store.write_manifest(path, manifest)

    def test_artifact_store_validates_manifest_references(self):
        with TemporaryDirectory() as directory:
            store = ArtifactStore(directory)
            attempt = store.reserve_attempt("task-1", 1)
            artifact = store.write_text_atomic(attempt / "execution.json", "{}\n")
            manifest = self.manifest(artifact_refs=(str(artifact),), state=RunState.COMPLETED)
            self.assertEqual(store.validate_manifest_references(manifest), (artifact.resolve(),))
            missing = self.manifest(artifact_refs=(str(attempt / "missing.json"),), state=RunState.COMPLETED)
            with self.assertRaises(FileNotFoundError):
                store.validate_manifest_references(missing)

    def test_required_artifacts_cannot_be_missing(self):
        manifest = self.manifest(
            state=RunState.BLOCKED,
            artifacts=(ArtifactRecord("execution", ArtifactStatus.MISSING, None, True, "not written"),),
            errors=(ErrorEnvelope(ErrorDomain.HARNESS, "WRITE_FAILED", "artifact write failed"),),
        )
        with self.assertRaises(ValueError):
            manifest.validate_lifecycle()

    def test_execution_artifact_must_match_manifest(self):
        manifest = self.manifest(state=RunState.COMPLETED)
        execution = {
            "run_id": manifest.attempt_id,
            "trial_id": manifest.trial_id,
            "attempt": manifest.attempt_number,
            "state": "COMPLETED",
            "error": None,
            "manifest_path": "manifest.json",
        }
        validate_execution_artifact_consistency(manifest, execution)
        execution["trial_id"] = "other-trial"
        with self.assertRaises(ValueError):
            validate_execution_artifact_consistency(manifest, execution)

    def test_load_attempt_requires_both_canonical_records(self):
        with TemporaryDirectory() as directory:
            store = ArtifactStore(directory)
            attempt = store.reserve_attempt("task-1", 1)
            with self.assertRaises(FileNotFoundError):
                load_attempt(attempt)

    def test_attempt_store_lists_validated_attempts_without_selecting_one(self):
        with TemporaryDirectory() as directory:
            store = ArtifactStore(directory)
            for number in (1, 2):
                attempt = store.reserve_attempt("task-1", number)
                execution = attempt / "execution.json"
                store.write_text_atomic(execution, "{}\n")
                manifest = self.manifest(
                    attempt_number=number,
                    attempt_id=derive_attempt_id(
                        trial_id="trial-task-treatment-1",
                        attempt_number=number,
                        configuration_digest="cfg-a",
                    ),
                    state=RunState.COMPLETED,
                    artifact_refs=(str(execution),),
                )
                # The index test uses canonical records with matching identity.
                payload = {
                    "run_id": manifest.attempt_id,
                    "trial_id": manifest.trial_id,
                    "attempt": number,
                    "state": "COMPLETED",
                    "error": None,
                    "manifest_path": str(attempt / "manifest.json"),
                    "trial_id": manifest.trial_id,
                }
                store.write_text_atomic(execution, json.dumps(payload))
                store.write_text_atomic(attempt / "manifest.json", manifest.to_json())
            snapshots = AttemptStore(directory).list_attempts("task-1")
            self.assertEqual([item.manifest.attempt_number for item in snapshots], [1, 2])

    def test_attempt_comparison_is_tri_state(self):
        left = self.manifest(budget_digest="budget-a")
        right = self.manifest(budget_digest="budget-a")
        self.assertEqual(compare_attempts(left, right).status, ComparabilityStatus.COMPARABLE)
        different = self.manifest(model="model-y", budget_digest="budget-a")
        self.assertEqual(compare_attempts(left, different).status, ComparabilityStatus.INCOMPARABLE)
        unknown = self.manifest(provider=None, budget_digest="budget-a")
        self.assertEqual(compare_attempts(left, unknown).status, ComparabilityStatus.INDETERMINATE)

    def test_comparison_report_does_not_aggregate_ineligible_pairs(self):
        first = self.manifest(budget_digest="budget-a")
        second = self.manifest(
            attempt_number=2,
            attempt_id=derive_attempt_id(trial_id=first.trial_id, attempt_number=2, configuration_digest="cfg-a"),
            budget_digest="budget-a",
        )
        third = self.manifest(model="model-y", budget_digest="budget-a")
        report = compare_attempt_collection((first, second, third))
        self.assertEqual(len(report.pairs), 3)
        self.assertEqual(len(report.comparable_pairs), 1)
        self.assertEqual(len(report.incomparable_pairs), 2)
        self.assertEqual(report.indeterminate_pairs, ())

    def test_evidence_extraction_preserves_unknown_metrics(self):
        snapshot = type("Snapshot", (), {
            "manifest": self.manifest(state=RunState.BLOCKED),
            "execution": {"model_usage": {"cost": 0.0}},
        })()
        evidence = evidence_from_snapshot(snapshot)
        self.assertEqual(evidence.execution_state, RunState.BLOCKED)
        self.assertIsNone(evidence.verification_state)
        self.assertIsNone(evidence.acceptance_decision)
        self.assertEqual(evidence.cost, 0.0)
        self.assertIsNone(evidence.total_tokens)
        self.assertIsNone(evidence.accepted)

    def test_execution_completion_does_not_imply_verification_or_acceptance(self):
        snapshot = type("Snapshot", (), {
            "manifest": self.manifest(state=RunState.COMPLETED),
            "execution": {"state": "COMPLETED"},
        })()
        evidence = evidence_from_snapshot(snapshot)
        self.assertEqual(evidence.execution_state, RunState.COMPLETED)
        self.assertIsNone(evidence.verification_state)
        self.assertIsNone(evidence.acceptance_decision)

    def test_verification_and_acceptance_evidence_have_independent_authorities(self):
        verification = VerificationEvidence("verifier-v1", "PASS", ("verification.json",))
        acceptance = AcceptanceEvidence("acceptance-v1", "ACCEPTED", ("acceptance.json",))
        self.assertNotEqual(verification.authority_identity, acceptance.authority_identity)
        self.assertEqual(verification.evidence_refs, ("verification.json",))
        self.assertEqual(acceptance.evidence_refs, ("acceptance.json",))

    def test_experiment_record_links_protocol_attempts_and_promotion(self):
        record = ExperimentRecord(
            experiment_id="exp-1",
            protocol_version="protocol-1",
            input_manifest_digest="input-digest",
            trial_ids=("trial-1",),
            attempt_ids=("attempt-1",),
            verification_refs=("verification://1",),
            acceptance_refs=("acceptance://1",),
            promotion_decision_ref="promotion://1",
            status="COMPLETED",
        )
        self.assertEqual(ExperimentRecord.from_json(record.to_json()).to_dict(), record.to_dict())
        with self.assertRaises(ValueError):
            ExperimentRecord("exp", "protocol", "digest", promotion_decision_ref="promotion://orphan")

    def test_experiment_record_loader_validates_attempts_and_refs(self):
        with TemporaryDirectory() as directory:
            artifact_store = ArtifactStore(directory)
            attempt_root = artifact_store.reserve_attempt("task-1", 1)
            execution_path = artifact_store.write_text_atomic(attempt_root / "execution.json", "{}\n")
            manifest = self.manifest(
                state=RunState.COMPLETED,
                artifact_refs=(str(execution_path),),
                state_history=(RunState.PLANNED, RunState.STARTED, RunState.EXECUTING, RunState.COMPLETED),
            )
            execution = {
                "run_id": manifest.attempt_id,
                "trial_id": manifest.trial_id,
                "attempt": 1,
                "state": "COMPLETED",
                "error": None,
                "manifest_path": str(attempt_root / "manifest.json"),
            }
            artifact_store.write_text_atomic(attempt_root / "execution.json", json.dumps(execution))
            artifact_store.write_text_atomic(attempt_root / "manifest.json", manifest.to_json())
            record = ExperimentRecord("exp-1", "protocol-1", "input", (manifest.trial_id,), (manifest.attempt_id,), ("verification://1",), ("acceptance://1",), "promotion://1", "COMPLETED")
            record_path = write_experiment_record(record, Path(directory) / "experiment.json")
            loaded = load_experiment_record(record_path, directory, promotion_attempt_id=manifest.attempt_id)
            self.assertEqual(len(loaded.attempts), 1)
            with self.assertRaises(FileExistsError):
                write_experiment_record(record, record_path)


if __name__ == "__main__":
    unittest.main()
