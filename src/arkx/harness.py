"""Executor-neutral contracts for reproducible harness runs.

This module records identity and failure boundaries.  It deliberately does not
execute providers, executors, sandboxes, verification, or acceptance.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from itertools import combinations
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = 1


class ErrorDomain(str, Enum):
    HARNESS = "HARNESS"
    PROVIDER = "PROVIDER"
    EXECUTOR = "EXECUTOR"
    SANDBOX = "SANDBOX"
    VERIFICATION = "VERIFICATION"
    ACCEPTANCE = "ACCEPTANCE"


class Retryability(str, Enum):
    RETRYABLE = "RETRYABLE"
    NOT_RETRYABLE = "NOT_RETRYABLE"
    UNKNOWN = "UNKNOWN"


class ArtifactStatus(str, Enum):
    PRESENT = "PRESENT"
    MISSING = "MISSING"


class ComparabilityStatus(str, Enum):
    COMPARABLE = "COMPARABLE"
    INCOMPARABLE = "INCOMPARABLE"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class ArtifactRecord:
    kind: str
    status: ArtifactStatus
    path: str | None
    required: bool = False
    reason: str | None = None

    def __post_init__(self) -> None:
        _require(self.kind, "artifact kind")
        if self.status is ArtifactStatus.PRESENT and not self.path:
            raise ValueError("present artifacts require a path")
        if self.status is ArtifactStatus.MISSING and not self.reason:
            raise ValueError("missing artifacts require a reason")

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "status": self.status.value,
            "path": self.path,
            "required": self.required,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ArtifactRecord":
        return cls(
            kind=str(value["kind"]),
            status=ArtifactStatus(value["status"]),
            path=value.get("path"),
            required=bool(value.get("required", False)),
            reason=value.get("reason"),
        )


class RunState(str, Enum):
    PLANNED = "PLANNED"
    STARTED = "STARTED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


_ALLOWED_TRANSITIONS: dict[RunState, frozenset[RunState]] = {
    RunState.PLANNED: frozenset({RunState.STARTED, RunState.BLOCKED}),
    RunState.STARTED: frozenset({RunState.EXECUTING, RunState.BLOCKED, RunState.FAILED}),
    RunState.EXECUTING: frozenset({RunState.COMPLETED, RunState.BLOCKED, RunState.FAILED, RunState.UNKNOWN}),
    RunState.COMPLETED: frozenset(),
    RunState.FAILED: frozenset(),
    RunState.BLOCKED: frozenset(),
    RunState.UNKNOWN: frozenset(),
}


def _json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _require(value: str, name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{name} must be non-empty")


def validate_transition(previous: RunState, current: RunState) -> None:
    if current not in _ALLOWED_TRANSITIONS[previous]:
        raise ValueError(f"invalid harness transition: {previous.value} -> {current.value}")


def validate_execution_artifact_consistency(manifest: "RunManifest", execution: Mapping[str, Any]) -> None:
    """Validate the legacy execution record against its common manifest."""

    if execution.get("run_id") != manifest.attempt_id:
        raise ValueError("execution run_id does not match manifest attempt_id")
    if execution.get("trial_id") != manifest.trial_id:
        raise ValueError("execution trial_id does not match manifest trial_id")
    if int(execution.get("attempt", 0)) != manifest.attempt_number:
        raise ValueError("execution attempt does not match manifest attempt_number")
    state_map = {"COMPLETED": RunState.COMPLETED, "EXECUTOR_FAILED": RunState.FAILED, "BLOCKED": RunState.BLOCKED}
    if state_map.get(execution.get("state")) is not manifest.state:
        raise ValueError("execution state does not match manifest state")
    execution_error = execution.get("error")
    if bool(manifest.errors) != bool(execution_error):
        raise ValueError("manifest and execution disagree about terminal error")
    if execution.get("manifest_path") is None:
        raise ValueError("execution artifact must point to its manifest")


@dataclass(frozen=True)
class RetryLineage:
    trial_id: str
    previous_attempt_id: str
    previous_attempt_number: int
    attempt_id: str
    attempt_number: int
    configuration_digest: str

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RetryLineage":
        lineage = cls(
            trial_id=str(value["trial_id"]),
            previous_attempt_id=str(value["previous_attempt_id"]),
            previous_attempt_number=int(value["previous_attempt_number"]),
            attempt_id=str(value["attempt_id"]),
            attempt_number=int(value["attempt_number"]),
            configuration_digest=str(value["configuration_digest"]),
        )
        if lineage.attempt_number != lineage.previous_attempt_number + 1:
            raise ValueError("retry lineage attempt numbers must be consecutive")
        expected_previous = derive_attempt_id(trial_id=lineage.trial_id, attempt_number=lineage.previous_attempt_number, configuration_digest=lineage.configuration_digest)
        expected_current = derive_attempt_id(trial_id=lineage.trial_id, attempt_number=lineage.attempt_number, configuration_digest=lineage.configuration_digest)
        if lineage.previous_attempt_id != expected_previous or lineage.attempt_id != expected_current:
            raise ValueError("retry lineage identities do not match its inputs")
        return lineage

    def to_dict(self) -> dict[str, Any]:
        return {
            "trial_id": self.trial_id,
            "previous_attempt_id": self.previous_attempt_id,
            "previous_attempt_number": self.previous_attempt_number,
            "attempt_id": self.attempt_id,
            "attempt_number": self.attempt_number,
            "configuration_digest": self.configuration_digest,
        }


@dataclass(frozen=True)
class RecoveryLineage:
    trial_id: str
    source_attempt_id: str
    source_attempt_number: int
    attempt_id: str
    attempt_number: int
    configuration_digest: str
    recovery_reference: str

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RecoveryLineage":
        lineage = cls(str(value["trial_id"]), str(value["source_attempt_id"]), int(value["source_attempt_number"]), str(value["attempt_id"]), int(value["attempt_number"]), str(value["configuration_digest"]), str(value["recovery_reference"]))
        if not lineage.recovery_reference.strip() or lineage.attempt_number != lineage.source_attempt_number + 1:
            raise ValueError("recovery lineage is incomplete or non-consecutive")
        expected_source = derive_attempt_id(trial_id=lineage.trial_id, attempt_number=lineage.source_attempt_number, configuration_digest=lineage.configuration_digest)
        expected_current = derive_attempt_id(trial_id=lineage.trial_id, attempt_number=lineage.attempt_number, configuration_digest=lineage.configuration_digest)
        if lineage.source_attempt_id != expected_source or lineage.attempt_id != expected_current:
            raise ValueError("recovery lineage identities do not match its inputs")
        return lineage

    def to_dict(self) -> dict[str, Any]:
        return {"trial_id": self.trial_id, "source_attempt_id": self.source_attempt_id, "source_attempt_number": self.source_attempt_number, "attempt_id": self.attempt_id, "attempt_number": self.attempt_number, "configuration_digest": self.configuration_digest, "recovery_reference": self.recovery_reference}


@dataclass(frozen=True)
class AttemptSnapshot:
    manifest: "RunManifest"
    execution: Mapping[str, Any]
    artifact_paths: tuple[Path, ...]
    retry_lineage: RetryLineage | None = None
    recovery_lineage: RecoveryLineage | None = None


@dataclass(frozen=True)
class AttemptComparison:
    status: ComparabilityStatus
    differing_fields: tuple[str, ...] = ()
    missing_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class PairComparison:
    left_attempt_id: str
    right_attempt_id: str
    comparison: AttemptComparison


@dataclass(frozen=True)
class ComparisonReport:
    pairs: tuple[PairComparison, ...]

    @property
    def comparable_pairs(self) -> tuple[PairComparison, ...]:
        return tuple(pair for pair in self.pairs if pair.comparison.status is ComparabilityStatus.COMPARABLE)

    @property
    def indeterminate_pairs(self) -> tuple[PairComparison, ...]:
        return tuple(pair for pair in self.pairs if pair.comparison.status is ComparabilityStatus.INDETERMINATE)

    @property
    def incomparable_pairs(self) -> tuple[PairComparison, ...]:
        return tuple(pair for pair in self.pairs if pair.comparison.status is ComparabilityStatus.INCOMPARABLE)


@dataclass(frozen=True)
class AuditedComparison:
    comparison: AttemptComparison
    left_audit: Any
    right_audit: Any


@dataclass(frozen=True)
class AttemptEvidence:
    attempt_id: str
    execution_state: RunState
    verification_evidence: "VerificationEvidence | None" = None
    acceptance_evidence: "AcceptanceEvidence | None" = None
    verification_state: str | None = None
    acceptance_decision: str | None = None
    accepted: bool | None = None
    verified: bool | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    cost: float | None = None
    wall_time_seconds: float | None = None


@dataclass(frozen=True)
class ExperimentRecord:
    experiment_id: str
    protocol_version: str
    input_manifest_digest: str
    trial_ids: tuple[str, ...] = ()
    attempt_ids: tuple[str, ...] = ()
    verification_refs: tuple[str, ...] = ()
    acceptance_refs: tuple[str, ...] = ()
    promotion_decision_ref: str | None = None
    status: str = "PLANNED"
    identity_digest: str | None = None
    capability_digest: str | None = None

    def __post_init__(self) -> None:
        for value, name in ((self.experiment_id, "experiment_id"), (self.protocol_version, "protocol_version"), (self.input_manifest_digest, "input_manifest_digest")):
            _require(value, name)
        for values, name in ((self.trial_ids, "trial_ids"), (self.attempt_ids, "attempt_ids"), (self.verification_refs, "verification_refs"), (self.acceptance_refs, "acceptance_refs")):
            if any(not value.strip() for value in values):
                raise ValueError(f"{name} must not contain empty references")
            if len(set(values)) != len(values):
                raise ValueError(f"{name} must be unique")
        if self.promotion_decision_ref and not self.attempt_ids:
            raise ValueError("promotion decision requires at least one attempt")
        if self.identity_digest is not None:
            _require(self.identity_digest, "identity_digest")
        if self.capability_digest is not None:
            _require(self.capability_digest, "capability_digest")

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "protocol_version": self.protocol_version,
            "input_manifest_digest": self.input_manifest_digest,
            "trial_ids": list(self.trial_ids),
            "attempt_ids": list(self.attempt_ids),
            "verification_refs": list(self.verification_refs),
            "acceptance_refs": list(self.acceptance_refs),
            "promotion_decision_ref": self.promotion_decision_ref,
            "status": self.status,
            "identity_digest": self.identity_digest,
            "capability_digest": self.capability_digest,
        }

    def to_json(self) -> str:
        return _json(self.to_dict())

    @classmethod
    def from_json(cls, value: str) -> "ExperimentRecord":
        payload = json.loads(value)
        return cls(**payload)


@dataclass(frozen=True)
class ExperimentSnapshot:
    record: ExperimentRecord
    attempts: tuple[AttemptSnapshot, ...]


def derive_experiment_identity_digest(attempts: tuple[AttemptSnapshot, ...]) -> str:
    """Derive a stable identity over execution-relevant attempt fields."""
    values = []
    for attempt in sorted(attempts, key=lambda item: item.manifest.attempt_id):
        manifest = attempt.manifest
        values.append({
            "attempt_id": manifest.attempt_id,
            "task_id": manifest.task_id,
            "task_revision": manifest.task_revision,
            "treatment": manifest.treatment,
            "executor": manifest.executor,
            "provider": manifest.provider,
            "model": manifest.model,
            "sandbox": manifest.sandbox,
            "repository_revision": manifest.repository_revision,
            "configuration_digest": manifest.configuration_digest,
            "budget_digest": manifest.budget_digest,
            "protocol_version": manifest.protocol_version,
        })
    return hashlib.sha256(_json({"attempts": values}).encode("utf-8")).hexdigest()[:16]


def _validate_experiment_reference(reference: str, attempts: tuple[AttemptSnapshot, ...]) -> None:
    if reference.startswith(("evidence://", "experiment://", "acceptance://", "verification://", "promotion://")):
        return
    available = {str(path) for attempt in attempts for path in attempt.artifact_paths}
    if reference not in available:
        raise ValueError(f"experiment reference is not present in validated artifacts: {reference}")


def validate_experiment_record(record: ExperimentRecord, attempts: tuple[AttemptSnapshot, ...], *, promotion_attempt_id: str | None = None) -> None:
    attempt_ids = {attempt.manifest.attempt_id for attempt in attempts}
    trial_ids = {attempt.manifest.trial_id for attempt in attempts}
    if set(record.attempt_ids) != attempt_ids:
        raise ValueError("experiment record attempt_ids do not match loaded attempts")
    if not set(record.trial_ids).issuperset(trial_ids):
        raise ValueError("experiment record is missing a loaded trial_id")
    for reference in record.verification_refs + record.acceptance_refs:
        _validate_experiment_reference(reference, attempts)
    if record.promotion_decision_ref:
        if promotion_attempt_id is None or promotion_attempt_id not in attempt_ids:
            raise ValueError("promotion decision is not bound to a recorded attempt")


def validate_experiment_record_audited(
    record: ExperimentRecord,
    attempts: tuple[AttemptSnapshot, ...],
    audits: tuple[Any, ...],
    *,
    promotion_attempt_id: str | None = None,
) -> None:
    """Require complete restored chains before treating an experiment as reproducible."""
    validate_experiment_record(record, attempts, promotion_attempt_id=promotion_attempt_id)
    if not record.identity_digest:
        raise ValueError("audited experiment requires identity_digest")
    if not record.capability_digest:
        raise ValueError("audited experiment requires capability_digest")
    if record.identity_digest != derive_experiment_identity_digest(attempts):
        raise ValueError("experiment identity_digest does not match audited attempts")
    if len(attempts) != len(audits):
        raise ValueError("audited experiment attempts and audits must have equal cardinality")
    chain_refs: set[str] = set()
    for attempt, audit in zip(attempts, audits):
        if audit.replay.run_id != attempt.manifest.attempt_id:
            raise ValueError("audited chain run_id does not match experiment attempt")
        if audit.protocol_version != record.protocol_version:
            raise ValueError("audited chain protocol_version does not match experiment")
        if audit.schema_version is None:
            raise ValueError("audited chain requires explicit event schema_version")
        manifest = attempt.manifest
        if audit.configuration_digest != manifest.configuration_digest:
            raise ValueError("audited chain configuration_digest does not match attempt")
        if audit.budget_digest != manifest.budget_digest:
            raise ValueError("audited chain budget_digest does not match attempt")
        if audit.treatment != manifest.treatment:
            raise ValueError("audited chain treatment does not match attempt")
        if audit.capability_digest != record.capability_digest:
            raise ValueError("audited chain capability_digest does not match experiment")
        if str(audit.integrity) != "ChainIntegrity.COMPLETE" and getattr(audit.integrity, "value", audit.integrity) != "COMPLETE":
            raise ValueError("experiment requires complete audited attempt chains")
        chain_refs.update(ref for ref in audit.chain.to_dict().values() if ref is not None)
    required_refs = set(record.verification_refs) | set(record.acceptance_refs)
    if record.promotion_decision_ref:
        required_refs.add(record.promotion_decision_ref)
    missing = sorted(required_refs - chain_refs)
    if missing:
        raise ValueError(f"experiment references are absent from audited chains: {','.join(missing)}")


def write_experiment_record(record: ExperimentRecord, path: str | Path) -> Path:
    target = Path(path)
    if target.exists():
        raise FileExistsError(f"experiment record already exists: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(record.to_json() + "\n", encoding="utf-8", newline="\n")
    temporary.replace(target)
    return target


def load_experiment_record(path: str | Path, artifact_root: str | Path, *, promotion_attempt_id: str | None = None) -> ExperimentSnapshot:
    record = ExperimentRecord.from_json(Path(path).read_text(encoding="utf-8"))
    attempts = tuple(
        attempt for attempt in AttemptStore(artifact_root).list_attempts()
        if attempt.manifest.attempt_id in set(record.attempt_ids)
    )
    validate_experiment_record(record, attempts, promotion_attempt_id=promotion_attempt_id)
    return ExperimentSnapshot(record, attempts)


@dataclass(frozen=True)
class VerificationEvidence:
    authority_identity: str | None
    state: str | None
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class AcceptanceEvidence:
    authority_identity: str | None
    decision: str | None
    evidence_refs: tuple[str, ...] = ()


def evidence_from_snapshot(snapshot: "AttemptSnapshot") -> AttemptEvidence:
    usage = snapshot.execution.get("model_usage")
    usage = usage if isinstance(usage, Mapping) else {}
    verification = snapshot.execution.get("verification")
    verification = verification if isinstance(verification, Mapping) else None
    acceptance = snapshot.execution.get("acceptance")
    acceptance = acceptance if isinstance(acceptance, Mapping) else None
    return AttemptEvidence(
        attempt_id=snapshot.manifest.attempt_id,
        execution_state=snapshot.manifest.state,
        verification_evidence=None if verification is None else VerificationEvidence(verification.get("authority_identity"), verification.get("state"), tuple(verification.get("evidence_refs", ()))),
        acceptance_evidence=None if acceptance is None else AcceptanceEvidence(acceptance.get("authority_identity"), acceptance.get("decision"), tuple(acceptance.get("evidence_refs", ()))),
        verification_state=snapshot.execution.get("verification_state") if verification is None else verification.get("state"),
        acceptance_decision=snapshot.execution.get("acceptance_decision") if acceptance is None else acceptance.get("decision"),
        accepted=snapshot.execution.get("accepted"),
        verified=snapshot.execution.get("verified"),
        input_tokens=usage.get("input_tokens"),
        output_tokens=usage.get("output_tokens"),
        total_tokens=usage.get("total_tokens"),
        cost=usage.get("cost"),
        wall_time_seconds=usage.get("wall_time_seconds"),
    )


def compare_attempts(left: "RunManifest", right: "RunManifest") -> AttemptComparison:
    fields = (
        "task_id", "task_revision", "treatment", "executor", "provider", "model",
        "sandbox", "configuration_digest", "budget_digest", "protocol_version",
    )
    differing = tuple(field for field in fields if getattr(left, field) is not None and getattr(right, field) is not None and getattr(left, field) != getattr(right, field))
    missing = tuple(field for field in fields if getattr(left, field) is None or getattr(right, field) is None)
    if differing:
        return AttemptComparison(ComparabilityStatus.INCOMPARABLE, differing_fields=differing, missing_fields=missing)
    if missing:
        return AttemptComparison(ComparabilityStatus.INDETERMINATE, missing_fields=missing)
    return AttemptComparison(ComparabilityStatus.COMPARABLE)


def compare_attempt_collection(manifests: tuple["RunManifest", ...]) -> ComparisonReport:
    pairs = tuple(
        PairComparison(left.attempt_id, right.attempt_id, compare_attempts(left, right))
        for left, right in combinations(manifests, 2)
    )
    return ComparisonReport(pairs)


def load_attempt(attempt_root: str | Path) -> AttemptSnapshot:
    root = Path(attempt_root).resolve()
    manifest_path = root / "manifest.json"
    execution_path = root / "execution.json"
    if not manifest_path.is_file() or not execution_path.is_file():
        raise FileNotFoundError("attempt requires manifest.json and execution.json")
    manifest = RunManifest.from_json(manifest_path.read_text(encoding="utf-8"))
    execution = json.loads(execution_path.read_text(encoding="utf-8"))
    manifest.validate_attempt_identity()
    manifest.validate_lifecycle()
    validate_execution_artifact_consistency(manifest, execution)
    lineage_path = root / "retry-lineage.json"
    lineage = None
    if lineage_path.is_file():
        lineage = RetryLineage.from_dict(json.loads(lineage_path.read_text(encoding="utf-8")))
        if lineage.trial_id != manifest.trial_id or lineage.attempt_id != manifest.attempt_id or lineage.attempt_number != manifest.attempt_number:
            raise ValueError("retry lineage does not match attempt manifest")
        if lineage.configuration_digest != manifest.configuration_digest:
            raise ValueError("retry lineage configuration does not match attempt manifest")
    recovery_path = root / "recovery-lineage.json"
    recovery_lineage = None
    if recovery_path.is_file():
        if lineage is not None:
            raise ValueError("attempt cannot contain both retry and recovery lineage")
        recovery_lineage = RecoveryLineage.from_dict(json.loads(recovery_path.read_text(encoding="utf-8")))
        if recovery_lineage.trial_id != manifest.trial_id or recovery_lineage.attempt_id != manifest.attempt_id or recovery_lineage.attempt_number != manifest.attempt_number:
            raise ValueError("recovery lineage does not match attempt manifest")
        if recovery_lineage.configuration_digest != manifest.configuration_digest:
            raise ValueError("recovery lineage configuration does not match attempt manifest")
    store = ArtifactStore(root.parents[1])
    artifact_paths = store.validate_manifest_references(manifest)
    return AttemptSnapshot(manifest, execution, artifact_paths, lineage, recovery_lineage)


class AttemptStore:
    """Read-only index over validated attempts; it never selects a winner."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def list_attempts(self, task_id: str | None = None) -> tuple[AttemptSnapshot, ...]:
        task_roots = [self.root / task_id] if task_id else [path for path in self.root.iterdir() if path.is_dir()]
        snapshots: list[AttemptSnapshot] = []
        for task_root in sorted(task_roots, key=lambda path: path.name):
            if not task_root.is_dir():
                continue
            for attempt_root in sorted(task_root.glob("attempt-*"), key=lambda path: path.name):
                if attempt_root.is_dir():
                    snapshots.append(load_attempt(attempt_root))
        return tuple(sorted(snapshots, key=lambda item: (item.manifest.task_id, item.manifest.attempt_number)))

    def load_audited(self, attempt_root: str | Path, event_log_path: str | Path, **outcomes: Any) -> Any:
        """Load an attempt and audit its event/outcome chain before consumption."""
        snapshot = load_attempt(attempt_root)
        from .event_log import audit_restored_chain
        return audit_restored_chain(event_log_path, snapshot, **outcomes)

    def compare_audited(
        self,
        left_root: str | Path,
        left_event_log: str | Path,
        right_root: str | Path,
        right_event_log: str | Path,
    ) -> AuditedComparison:
        """Compare attempts only after both persisted chains are complete."""
        from .event_log import ChainIntegrity
        left = load_attempt(left_root)
        right = load_attempt(right_root)
        left_audit = self.load_audited(left_root, left_event_log)
        right_audit = self.load_audited(right_root, right_event_log)
        if left_audit.integrity is not ChainIntegrity.COMPLETE or right_audit.integrity is not ChainIntegrity.COMPLETE:
            raise ValueError("audited comparison requires complete persisted chains")
        return AuditedComparison(compare_attempts(left.manifest, right.manifest), left_audit, right_audit)


class ArtifactStore:
    """Small append-only store for one harness artifact root."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def reserve_attempt(self, task_id: str, attempt_number: int) -> Path:
        _require(task_id, "task_id")
        if attempt_number < 1:
            raise ValueError("attempt_number must be positive")
        path = (self.root / task_id / f"attempt-{attempt_number}").resolve()
        if self.root not in path.parents:
            raise ValueError("task_id escapes artifact root")
        if path.exists():
            raise FileExistsError(f"attempt artifact already exists: {path}")
        path.mkdir(parents=True)
        return path

    def reserve_retry_attempt(
        self,
        task_id: str,
        *,
        trial_id: str,
        previous_attempt_id: str,
        previous_attempt_number: int,
        configuration_digest: str,
        budget_ledger: Mapping[str, Any] | None = None,
    ) -> Path:
        """Reserve a new retry directory and persist its immutable lineage."""
        if previous_attempt_number < 1:
            raise ValueError("previous_attempt_number must be positive")
        expected_previous = derive_attempt_id(trial_id=trial_id, attempt_number=previous_attempt_number, configuration_digest=configuration_digest)
        if previous_attempt_id != expected_previous:
            raise ValueError("previous attempt identity does not match lineage inputs")
        if budget_ledger is not None:
            consumed = tuple(str(value) for value in budget_ledger.get("consumed_attempts", ()))
            budget = budget_ledger.get("budget", {})
            if previous_attempt_id not in consumed:
                raise ValueError("budget ledger does not contain previous retry attempt")
            max_attempts = budget.get("max_attempts") if isinstance(budget, Mapping) else None
            if max_attempts is not None and len(consumed) + 1 > int(max_attempts):
                raise ValueError("retry attempt exceeds execution budget")
        next_number = previous_attempt_number + 1
        path = self.reserve_attempt(task_id, next_number)
        next_id = derive_attempt_id(trial_id=trial_id, attempt_number=next_number, configuration_digest=configuration_digest)
        self.write_text_atomic(path / "retry-lineage.json", _json({
            "trial_id": trial_id,
            "previous_attempt_id": previous_attempt_id,
            "previous_attempt_number": previous_attempt_number,
            "attempt_id": next_id,
            "attempt_number": next_number,
            "configuration_digest": configuration_digest,
        }))
        if budget_ledger is not None:
            updated_ledger = dict(budget_ledger)
            updated_ledger["consumed_attempts"] = [*tuple(str(value) for value in budget_ledger.get("consumed_attempts", ())), next_id]
            self.write_text_atomic(path / "budget-ledger.json", _json(updated_ledger))
        return path

    def reserve_recovery_attempt(
        self,
        task_id: str,
        *,
        trial_id: str,
        source_attempt_id: str,
        source_attempt_number: int,
        configuration_digest: str,
        recovery_reference: str,
        budget_ledger: Mapping[str, Any] | None = None,
    ) -> Path:
        """Reserve a fresh recovery attempt and persist its causal lineage."""
        if not recovery_reference.strip():
            raise ValueError("recovery_reference must be non-empty")
        if source_attempt_number < 1:
            raise ValueError("source_attempt_number must be positive")
        expected_source = derive_attempt_id(trial_id=trial_id, attempt_number=source_attempt_number, configuration_digest=configuration_digest)
        if source_attempt_id != expected_source:
            raise ValueError("source attempt identity does not match recovery lineage")
        if budget_ledger is not None:
            consumed = tuple(str(value) for value in budget_ledger.get("consumed_attempts", ()))
            budget = budget_ledger.get("budget", {})
            if source_attempt_id not in consumed:
                raise ValueError("budget ledger does not contain source recovery attempt")
            max_attempts = budget.get("max_attempts") if isinstance(budget, Mapping) else None
            if max_attempts is not None and len(consumed) + 1 > int(max_attempts):
                raise ValueError("recovery attempt exceeds execution budget")
        next_number = source_attempt_number + 1
        path = self.reserve_attempt(task_id, next_number)
        next_id = derive_attempt_id(trial_id=trial_id, attempt_number=next_number, configuration_digest=configuration_digest)
        self.write_text_atomic(path / "recovery-lineage.json", _json({
            "trial_id": trial_id,
            "source_attempt_id": source_attempt_id,
            "source_attempt_number": source_attempt_number,
            "attempt_id": next_id,
            "attempt_number": next_number,
            "configuration_digest": configuration_digest,
            "recovery_reference": recovery_reference,
        }))
        if budget_ledger is not None:
            updated_ledger = dict(budget_ledger)
            updated_ledger["consumed_attempts"] = [*tuple(str(value) for value in budget_ledger.get("consumed_attempts", ())), next_id]
            self.write_text_atomic(path / "budget-ledger.json", _json(updated_ledger))
        return path

    def write_text_atomic(self, path: str | Path, content: str) -> Path:
        target = Path(path).resolve()
        if self.root not in target.parents:
            raise ValueError("artifact path escapes artifact root")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_text(content, encoding="utf-8", newline="\n")
        temporary.replace(target)
        return target

    def write_manifest(self, attempt_root: str | Path, manifest: "RunManifest") -> Path:
        """Validate and atomically persist the current manifest snapshot."""
        root = Path(attempt_root).resolve()
        if self.root not in root.parents or not root.is_dir():
            raise ValueError("attempt root is outside artifact store")
        manifest.validate_attempt_identity()
        manifest.validate_lifecycle()
        recovery_path = root / "recovery-lineage.json"
        if recovery_path.is_file():
            lineage = RecoveryLineage.from_dict(json.loads(recovery_path.read_text(encoding="utf-8")))
            if lineage.trial_id != manifest.trial_id or lineage.attempt_id != manifest.attempt_id or lineage.attempt_number != manifest.attempt_number or lineage.configuration_digest != manifest.configuration_digest:
                raise ValueError("recovery lineage does not match manifest being written")
        budget_path = root / "budget-ledger.json"
        if budget_path.is_file():
            persisted_ledger = json.loads(budget_path.read_text(encoding="utf-8"))
            if manifest.budget_ledger != persisted_ledger:
                raise ValueError("manifest budget ledger does not match persisted attempt ledger")
        return self.write_text_atomic(root / "manifest.json", manifest.to_json())

    def validate_manifest_references(self, manifest: "RunManifest") -> tuple[Path, ...]:
        if manifest.state is not RunState.PLANNED and not manifest.artifact_refs:
            raise ValueError("non-planned manifests require artifact references")
        resolved: list[Path] = []
        for reference in manifest.artifact_refs:
            path = Path(reference).resolve()
            if self.root not in path.parents:
                raise ValueError("manifest artifact reference escapes artifact root")
            if not path.is_file():
                raise FileNotFoundError(f"manifest artifact is missing: {path}")
            resolved.append(path)
        return tuple(resolved)


@dataclass(frozen=True)
class ErrorEnvelope:
    domain: ErrorDomain
    code: str
    message: str
    retryability: Retryability = Retryability.UNKNOWN
    raw_evidence_refs: tuple[str, ...] = ()
    attempt_number: int | None = None
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require(self.code, "error code")
        _require(self.message, "error message")
        if self.attempt_number is not None and self.attempt_number < 1:
            raise ValueError("attempt_number must be positive when present")
        refs = tuple(sorted(set(self.raw_evidence_refs)))
        if any(not ref.strip() for ref in refs):
            raise ValueError("raw evidence references must be non-empty")
        object.__setattr__(self, "raw_evidence_refs", refs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "domain": self.domain.value,
            "code": self.code,
            "message": self.message,
            "retryability": self.retryability.value,
            "raw_evidence_refs": list(self.raw_evidence_refs),
            "attempt_number": self.attempt_number,
        }

    def to_json(self) -> str:
        return _json(self.to_dict())

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ErrorEnvelope":
        return cls(
            domain=ErrorDomain(value["domain"]),
            code=str(value["code"]),
            message=str(value["message"]),
            retryability=Retryability(value.get("retryability", Retryability.UNKNOWN.value)),
            raw_evidence_refs=tuple(value.get("raw_evidence_refs", ())),
            attempt_number=value.get("attempt_number"),
            schema_version=int(value.get("schema_version", 0)),
        )


@dataclass(frozen=True)
class LifecycleEvent:
    state: RunState
    timestamp: str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
        refs = tuple(sorted(set(self.evidence_refs)))
        if any(not ref.strip() for ref in refs):
            raise ValueError("lifecycle evidence references must be non-empty")
        object.__setattr__(self, "evidence_refs", refs)

    def to_dict(self) -> dict[str, Any]:
        return {"state": self.state.value, "timestamp": self.timestamp, "evidence_refs": list(self.evidence_refs)}

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "LifecycleEvent":
        return cls(RunState(value["state"]), str(value["timestamp"]), tuple(value.get("evidence_refs", ())))


@dataclass(frozen=True)
class RunManifest:
    """One immutable execution attempt, distinct from its experiment/trial."""

    experiment_id: str
    trial_id: str
    attempt_id: str
    attempt_number: int
    task_id: str
    task_revision: str | None
    treatment: str
    executor: str | None
    provider: str | None
    model: str | None
    sandbox: str | None
    repository_revision: str | None
    configuration_digest: str | None
    protocol_version: str | None
    budget_digest: str | None = None
    state: RunState = RunState.PLANNED
    state_history: tuple[RunState, ...] = ()
    lifecycle_events: tuple[LifecycleEvent, ...] = ()
    artifacts: tuple[ArtifactRecord, ...] = ()
    artifact_refs: tuple[str, ...] = ()
    errors: tuple[ErrorEnvelope, ...] = ()
    schema_version: int = SCHEMA_VERSION
    budget_ledger: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        for name in (
            "experiment_id", "trial_id", "attempt_id", "task_id", "treatment",
        ):
            _require(getattr(self, name), name)
        if self.attempt_number < 1:
            raise ValueError("attempt_number must be positive")
        refs = tuple(sorted(set(self.artifact_refs)))
        if any(not ref.strip() for ref in refs):
            raise ValueError("artifact references must be non-empty")
        object.__setattr__(self, "artifact_refs", refs)
        object.__setattr__(self, "errors", tuple(self.errors))
        object.__setattr__(self, "state_history", tuple(self.state_history))
        object.__setattr__(self, "lifecycle_events", tuple(self.lifecycle_events))
        object.__setattr__(self, "artifacts", tuple(self.artifacts))
        if self.budget_ledger is not None:
            object.__setattr__(self, "budget_ledger", dict(self.budget_ledger))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "experiment_id": self.experiment_id,
            "trial_id": self.trial_id,
            "attempt_id": self.attempt_id,
            "attempt_number": self.attempt_number,
            "task_id": self.task_id,
            "task_revision": self.task_revision,
            "treatment": self.treatment,
            "executor": self.executor,
            "provider": self.provider,
            "model": self.model,
            "sandbox": self.sandbox,
            "repository_revision": self.repository_revision,
            "configuration_digest": self.configuration_digest,
            "protocol_version": self.protocol_version,
            "budget_digest": self.budget_digest,
            "state": self.state.value,
            "state_history": [state.value for state in self.state_history],
            "lifecycle_events": [event.to_dict() for event in self.lifecycle_events],
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "artifact_refs": list(self.artifact_refs),
            "errors": [error.to_dict() for error in self.errors],
            "budget_ledger": self.budget_ledger,
        }

    def to_json(self) -> str:
        return _json(self.to_dict())

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "RunManifest":
        schema_version = int(value.get("schema_version", 0))
        if schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported harness manifest schema: {schema_version}")
        errors = tuple(ErrorEnvelope.from_dict(item) for item in value.get("errors", ()))
        return cls(
            experiment_id=str(value["experiment_id"]),
            trial_id=str(value["trial_id"]),
            attempt_id=str(value["attempt_id"]),
            attempt_number=int(value["attempt_number"]),
            task_id=str(value["task_id"]),
            task_revision=value.get("task_revision"),
            treatment=str(value["treatment"]),
            executor=value.get("executor"),
            provider=value.get("provider"),
            model=value.get("model"),
            sandbox=value.get("sandbox"),
            repository_revision=value.get("repository_revision"),
            configuration_digest=value.get("configuration_digest"),
            protocol_version=value.get("protocol_version"),
            budget_digest=value.get("budget_digest"),
            state=RunState(value["state"]),
            state_history=tuple(RunState(item) for item in value.get("state_history", ())),
            lifecycle_events=tuple(LifecycleEvent.from_dict(item) for item in value.get("lifecycle_events", ())),
            artifacts=tuple(ArtifactRecord.from_dict(item) for item in value.get("artifacts", ())),
            artifact_refs=tuple(value.get("artifact_refs", ())),
            errors=errors,
            schema_version=schema_version,
            budget_ledger=value.get("budget_ledger"),
        )

    @classmethod
    def from_json(cls, value: str) -> "RunManifest":
        return cls.from_dict(json.loads(value))

    def validate_attempt_identity(self) -> None:
        if self.configuration_digest is None:
            raise ValueError("configuration_digest is required to validate attempt identity")
        expected = derive_attempt_id(
            trial_id=self.trial_id,
            attempt_number=self.attempt_number,
            configuration_digest=self.configuration_digest,
        )
        if self.attempt_id != expected:
            raise ValueError("attempt_id does not match trial, attempt number, and configuration")

    def with_budget_ledger(self, ledger: Mapping[str, Any]) -> "RunManifest":
        """Return a manifest snapshot bound to this attempt's budget ledger."""
        consumed = tuple(ledger.get("consumed_attempts", ()))
        if self.attempt_id not in consumed:
            raise ValueError("budget ledger does not contain manifest attempt_id")
        ledger_digest = ledger.get("budget_digest")
        if self.budget_digest is not None and ledger_digest != self.budget_digest:
            raise ValueError("budget ledger digest does not match manifest budget_digest")
        return replace(self, budget_ledger=dict(ledger))

    def validate_lifecycle(self) -> None:
        terminal = {RunState.COMPLETED, RunState.FAILED, RunState.BLOCKED, RunState.UNKNOWN}
        if self.state is RunState.COMPLETED and self.errors:
            raise ValueError("completed runs cannot contain terminal errors")
        if self.state in {RunState.FAILED, RunState.BLOCKED} and not self.errors:
            raise ValueError(f"{self.state.value.lower()} runs require structured errors")
        if self.state is RunState.PLANNED and self.artifact_refs:
            raise ValueError("planned runs cannot reference execution artifacts")
        if self.state not in terminal and self.errors:
            raise ValueError(f"{self.state.value.lower()} runs cannot contain terminal errors")
        if self.state_history:
            if self.state_history[0] is not RunState.PLANNED:
                raise ValueError("state history must start at PLANNED")
            if self.state_history[-1] is not self.state:
                raise ValueError("state history must end at the manifest state")
            for previous, current in zip(self.state_history, self.state_history[1:]):
                validate_transition(previous, current)
        if self.lifecycle_events:
            states = tuple(event.state for event in self.lifecycle_events)
            if states != self.state_history:
                raise ValueError("lifecycle event states must match state history")
            timestamps = [datetime.fromisoformat(event.timestamp.replace("Z", "+00:00")) for event in self.lifecycle_events]
            if timestamps != sorted(timestamps):
                raise ValueError("lifecycle event timestamps must be monotonic")
        for artifact in self.artifacts:
            if artifact.required and artifact.status is not ArtifactStatus.PRESENT:
                raise ValueError(f"required artifact is not present: {artifact.kind}")


def derive_attempt_id(*, trial_id: str, attempt_number: int, configuration_digest: str) -> str:
    """Derive a stable, collision-resistant id without timestamps or fallbacks."""

    _require(trial_id, "trial_id")
    _require(configuration_digest, "configuration_digest")
    if attempt_number < 1:
        raise ValueError("attempt_number must be positive")
    payload = f"{trial_id}\n{attempt_number}\n{configuration_digest}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:24]
