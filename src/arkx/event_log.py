"""Persistent, append-only event log for executor-neutral lifecycle telemetry."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Mapping

from dataclasses import dataclass
from enum import Enum

from .contracts import Event, EventType
from .harness import AcceptanceEvidence, AttemptSnapshot, RunManifest, VerificationEvidence
from .outcomes import AcceptanceResult, VerificationResult, validate_outcome_references
from .promotion import PromotionDecision
from .recovery import RecoveryPlan


EVENT_SCHEMA_VERSION = 1


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class EventLog:
    """Serial event log; it does not interpret events or choose outcomes."""

    def __init__(self, path: str | Path, *, run_id: str) -> None:
        if not run_id.strip():
            raise ValueError("run_id must be non-empty")
        self.path = Path(path).resolve()
        self.run_id = run_id

    def read(self) -> tuple[Event, ...]:
        if not self.path.exists():
            return ()
        events: list[Event] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            event = Event.from_dict(json.loads(line))
            self._validate_event(event, events[-1] if events else None)
            events.append(event)
        return tuple(events)

    def append(self, event: Event) -> None:
        events = list(self.read())
        self._validate_event(event, events[-1] if events else None)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        content = "".join(json.dumps(item.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for item in (*events, event))
        temporary = self.path.with_name(self.path.name + ".tmp")
        temporary.write_text(content, encoding="utf-8", newline="\n")
        temporary.replace(self.path)

    def append_stage(self, *, timestamp: str, event_type: EventType, stage: str, ref: str, data: dict | None = None) -> bool:
        """Persist one causal stage reference; identical repeats are idempotent."""
        if stage not in {"request", "plan", "preflight", "provider_preflight", "sandbox_preflight", "execution", "recovery", "verification", "acceptance", "promotion"}:
            raise ValueError("unknown lifecycle stage")
        if not ref.strip():
            raise ValueError("stage reference must be non-empty")
        current = replay_chain(self.read(), run_id=self.run_id)
        current_ref = current.to_dict()[f"{stage}_ref"]
        if current_ref == ref:
            return False
        if current_ref is not None:
            raise ValueError("stage reference changed during append")
        payload = dict(data or {})
        payload.update({"stage": stage, "ref": ref})
        self.append(Event(timestamp, event_type, self.run_id, payload))
        return True

    def append_terminal(self, *, timestamp: str, status: str, error_code: str | None = None, data: dict | None = None) -> bool:
        """Persist one terminal lifecycle fact without inferring later stages."""
        if not status.strip():
            raise ValueError("terminal status must be non-empty")
        current = self.read()
        terminals = [event for event in current if event.type is EventType.TASK_FINISHED]
        if terminals:
            previous = terminals[-1].data.get("status")
            if previous != status:
                raise ValueError("terminal status changed during append")
            previous_error = terminals[-1].data.get("error_code")
            if previous_error != error_code:
                raise ValueError("terminal error code changed during append")
            return False
        payload = dict(data or {})
        payload["status"] = status
        if error_code is not None:
            payload["error_code"] = error_code
        self.append(Event(timestamp, EventType.TASK_FINISHED, self.run_id, payload))
        return True

    def _validate_event(self, event: Event, previous: Event | None) -> None:
        if event.run_id != self.run_id:
            raise ValueError("event run_id does not match log")
        current_time = _time(event.timestamp)
        if previous is not None and current_time < _time(previous.timestamp):
            raise ValueError("event timestamps must be monotonic")


@dataclass(frozen=True)
class ReplayState:
    run_id: str
    event_count: int
    declared_status: str | None = None
    executor_invocations: int = 0
    retry_count: int = 0
    evidence_refs: tuple[str, ...] = ()
    verification_state: str | None = None
    acceptance_decision: str | None = None
    execution_outcome: str | None = None
    preflight_status: str | None = None
    promotion_status: str | None = None
    error_codes: tuple[str, ...] = ()
    budget_ledger: Mapping[str, Any] | None = None
    recovery_source_attempt_id: str | None = None


@dataclass(frozen=True)
class ReplayChain:
    request_ref: str | None = None
    plan_ref: str | None = None
    execution_ref: str | None = None
    verification_ref: str | None = None
    acceptance_ref: str | None = None
    promotion_ref: str | None = None
    recovery_ref: str | None = None
    preflight_ref: str | None = None
    provider_preflight_ref: str | None = None
    sandbox_preflight_ref: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "request_ref": self.request_ref,
            "plan_ref": self.plan_ref,
            "preflight_ref": self.preflight_ref,
            "provider_preflight_ref": self.provider_preflight_ref,
            "sandbox_preflight_ref": self.sandbox_preflight_ref,
            "execution_ref": self.execution_ref,
            "recovery_ref": self.recovery_ref,
            "verification_ref": self.verification_ref,
            "acceptance_ref": self.acceptance_ref,
            "promotion_ref": self.promotion_ref,
        }


@dataclass(frozen=True)
class ReferenceReport:
    present: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()
    indeterminate: tuple[str, ...] = ()

    def status(self) -> str:
        if self.missing:
            return "MISSING"
        if self.indeterminate:
            return "INDETERMINATE"
        return "PRESENT"


@dataclass(frozen=True)
class RestoredChainAudit:
    chain: ReplayChain
    replay: ReplayState
    references: ReferenceReport
    integrity: ChainIntegrity
    protocol_version: str | None = None
    schema_version: int | None = None
    configuration_digest: str | None = None
    budget_digest: str | None = None
    treatment: str | None = None
    capability_digest: str | None = None
    resume_decision: ResumeDecision | None = None
    budget_ledger: Mapping[str, Any] | None = None


class ChainIntegrity(str, Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    INCONSISTENT = "INCONSISTENT"


class ResumeAction(str, Enum):
    TERMINAL = "TERMINAL"
    RESUME_VERIFICATION = "RESUME_VERIFICATION"
    RESUME_ACCEPTANCE = "RESUME_ACCEPTANCE"
    RESUME_PROMOTION = "RESUME_PROMOTION"
    RESTART_REQUIRED = "RESTART_REQUIRED"
    REPLAN_REQUIRED = "REPLAN_REQUIRED"


@dataclass(frozen=True)
class ResumeDecision:
    action: ResumeAction
    reason: str
    source_ref: str | None = None


def decide_resume(chain: ReplayChain, replay: ReplayState) -> ResumeDecision:
    """Decide a safe resume boundary without executing or inferring missing facts."""
    if replay.declared_status is not None:
        return ResumeDecision(ResumeAction.TERMINAL, "terminal event already persisted")
    if chain.recovery_ref is not None and chain.execution_ref is None:
        return ResumeDecision(ResumeAction.REPLAN_REQUIRED, "recovery exists without a new execution attempt", chain.recovery_ref)
    if chain.execution_ref is None:
        return ResumeDecision(ResumeAction.RESTART_REQUIRED, "execution evidence is absent; prior execution cannot be inferred", chain.plan_ref)
    if chain.verification_ref is None:
        return ResumeDecision(ResumeAction.RESUME_VERIFICATION, "execution is persisted without verification", chain.execution_ref)
    if chain.acceptance_ref is None:
        return ResumeDecision(ResumeAction.RESUME_ACCEPTANCE, "verification is persisted without acceptance", chain.verification_ref)
    if chain.promotion_ref is None:
        return ResumeDecision(ResumeAction.RESUME_PROMOTION, "acceptance is persisted without promotion", chain.acceptance_ref)
    return ResumeDecision(ResumeAction.TERMINAL, "complete outcome chain is persisted", chain.promotion_ref)


def assess_chain_integrity(chain: ReplayChain, references: ReferenceReport) -> ChainIntegrity:
    values = chain.to_dict()
    if references.missing:
        return ChainIntegrity.INCONSISTENT
    required = (chain.request_ref, chain.plan_ref, chain.execution_ref, chain.verification_ref, chain.acceptance_ref, chain.promotion_ref)
    if any(value is None for value in required) or references.indeterminate:
        return ChainIntegrity.INCOMPLETE
    return ChainIntegrity.COMPLETE


def replay_events(events: tuple[Event, ...] | list[Event], *, run_id: str) -> ReplayState:
    """Reduce persisted facts without executing or evaluating the task."""
    log = EventLog(".", run_id=run_id)
    previous = None
    refs: list[str] = []
    invocations = 0
    retries = 0
    declared_status = None
    verification_state = None
    acceptance_decision = None
    execution_outcome = None
    preflight_status = None
    promotion_status = None
    error_codes: list[str] = []
    budget_ledger: Mapping[str, Any] | None = None
    recovery_source_attempt_id: str | None = None
    for event in events:
        log._validate_event(event, previous)
        previous = event
        if event.type is EventType.EXECUTOR_STARTED:
            invocations += 1
        elif event.type is EventType.RETRY:
            retries += 1
        elif event.type is EventType.EVIDENCE_ADDED:
            if event.data.get("ref") is not None:
                refs.append(str(event.data["ref"]))
            refs.extend(str(ref) for ref in event.data.get("refs", []))
            if event.data.get("verification_state") is not None:
                verification_state = str(event.data["verification_state"])
            if event.data.get("acceptance_decision") is not None:
                acceptance_decision = str(event.data["acceptance_decision"])
            if event.data.get("execution_outcome") is not None:
                execution_outcome = str(event.data["execution_outcome"])
            if event.data.get("preflight_status") is not None:
                preflight_status = str(event.data["preflight_status"])
            if event.data.get("promotion_status") is not None:
                promotion_status = str(event.data["promotion_status"])
            if event.data.get("error_code") is not None:
                error_codes.append(str(event.data["error_code"]))
            if event.data.get("budget_ledger") is not None:
                candidate = event.data["budget_ledger"]
                if not isinstance(candidate, Mapping):
                    raise ValueError("budget_ledger event data must be a mapping")
                if budget_ledger is not None and dict(budget_ledger) != dict(candidate):
                    raise ValueError("budget ledger changed during replay")
                budget_ledger = dict(candidate)
        elif event.type is EventType.TASK_FINISHED:
            value = event.data.get("status")
            declared_status = None if value is None else str(value)
            if event.data.get("error_code") is not None:
                error_codes.append(str(event.data["error_code"]))
        if event.type is EventType.REPLAN and event.data.get("source_attempt_id") is not None:
            candidate_source = str(event.data["source_attempt_id"])
            if recovery_source_attempt_id is not None and recovery_source_attempt_id != candidate_source:
                raise ValueError("recovery source attempt changed during replay")
            recovery_source_attempt_id = candidate_source
    return ReplayState(run_id, len(events), declared_status, invocations, retries, tuple(refs), verification_state, acceptance_decision, execution_outcome, preflight_status, promotion_status, tuple(sorted(set(error_codes))), budget_ledger, recovery_source_attempt_id)


def replay_chain(events: tuple[Event, ...] | list[Event], *, run_id: str) -> ReplayChain:
    """Reconstruct explicit stage references without filling missing stages."""
    replay_events(events, run_id=run_id)
    values: dict[str, str | None] = {stage: None for stage in ("request", "plan", "preflight", "provider_preflight", "sandbox_preflight", "execution", "recovery", "verification", "acceptance", "promotion")}
    order = {stage: index for index, stage in enumerate(values)}
    highest = -1
    for event in events:
        stage = event.data.get("stage")
        ref = event.data.get("ref")
        if stage is None:
            continue
        if stage not in order or ref is None or not str(ref).strip():
            raise ValueError("stage events require a known stage and non-empty ref")
        if order[stage] < highest:
            raise ValueError("stage references are out of causal order")
        if values[stage] is not None and values[stage] != str(ref):
            raise ValueError("stage reference changed during replay")
        highest = order[stage]
        values[stage] = str(ref)
    return ReplayChain(**{f"{stage}_ref": values[stage] for stage in values})


def classify_chain_references(chain: ReplayChain, *, available_refs: set[str] | None = None) -> ReferenceReport:
    refs = tuple(ref for ref in chain.to_dict().values() if ref is not None)
    if available_refs is None:
        return ReferenceReport(indeterminate=tuple(sorted(set(refs))))
    present = tuple(sorted(set(ref for ref in refs if ref in available_refs)))
    missing = tuple(sorted(set(ref for ref in refs if ref not in available_refs)))
    return ReferenceReport(present=present, missing=missing)


def classify_snapshot_chain_references(snapshot: AttemptSnapshot, chain: ReplayChain) -> ReferenceReport:
    """Classify chain refs only against artifacts validated by an attempt snapshot."""
    available = {str(path) for path in snapshot.artifact_paths}
    available.update(snapshot.manifest.artifact_refs)
    return classify_chain_references(chain, available_refs=available)


def validate_replay_against_manifest(manifest: RunManifest, replay: ReplayState) -> None:
    """Reject divergence between persisted manifest state and replayed facts."""
    if manifest.attempt_id != replay.run_id:
        raise ValueError("replay run_id does not match manifest attempt_id")
    if replay.declared_status is None:
        return
    if replay.declared_status != manifest.state.value:
        raise ValueError("replayed declared status does not match manifest state")


def validate_terminal_replay(
    replay: ReplayState,
    *,
    expected_status: str,
    expected_error_code: str | None = None,
) -> None:
    """Check the terminal fact without inferring a missing terminal event."""
    if not expected_status.strip():
        raise ValueError("expected terminal status must be non-empty")
    if replay.declared_status is None:
        raise ValueError("terminal status is missing from replay")
    if replay.declared_status != expected_status:
        raise ValueError("replayed terminal status does not match expected status")
    if expected_error_code is not None and expected_error_code not in replay.error_codes:
        raise ValueError("replayed terminal error code does not match expected error")


def validate_replay_outcomes(
    replay: ReplayState,
    *,
    verification: VerificationEvidence | None = None,
    acceptance: AcceptanceEvidence | None = None,
) -> None:
    """Check explicitly replayed outcomes against independent evidence only."""
    if verification is not None and replay.verification_state is not None and replay.verification_state != verification.state:
        raise ValueError("replayed verification state does not match evidence")
    if acceptance is not None and replay.acceptance_decision is not None and replay.acceptance_decision != acceptance.decision:
        raise ValueError("replayed acceptance decision does not match evidence")


def validate_replay_telemetry(
    replay: ReplayState,
    *,
    execution: object | None = None,
    verification: VerificationResult | None = None,
    acceptance: AcceptanceResult | None = None,
    promotion: PromotionDecision | None = None,
) -> None:
    """Reject persisted telemetry that diverges from loaded result objects."""
    if execution is not None:
        state = getattr(execution, "state", None)
        expected = getattr(state, "value", state)
        if replay.execution_outcome is not None and replay.execution_outcome not in (str(expected), "COMPLETED" if str(expected) == "COMPLETED" else str(expected)):
            raise ValueError("replayed execution outcome does not match execution result")
        error = getattr(execution, "error", None)
        if error is not None and replay.error_codes:
            code = getattr(error, "code", None)
            if code is not None and code not in replay.error_codes:
                raise ValueError("replayed error code does not match execution result")
    if verification is not None and replay.verification_state is not None and replay.verification_state != verification.state.value:
        raise ValueError("replayed verification state does not match verification result")
    if acceptance is not None and replay.acceptance_decision is not None and replay.acceptance_decision != acceptance.decision.value:
        raise ValueError("replayed acceptance decision does not match acceptance result")
    if promotion is not None and replay.promotion_status is not None and replay.promotion_status != promotion.status.value:
        raise ValueError("replayed promotion status does not match promotion decision")


def validate_final_chain(
    *,
    attempt_id: str,
    verification_ref: str,
    acceptance_ref: str,
    promotion_ref: str,
    promotion: PromotionDecision,
) -> None:
    if promotion.attempt_id != attempt_id:
        raise ValueError("promotion decision does not match attempt")
    if promotion.reference != promotion_ref:
        raise ValueError("promotion reference does not match decision")
    if promotion.acceptance is not None and promotion.acceptance.reference != acceptance_ref:
        raise ValueError("promotion acceptance does not match acceptance reference")
    if not verification_ref.strip() or not acceptance_ref.strip():
        raise ValueError("verification and acceptance references must be non-empty")


def validate_outcome_chain(
    chain: ReplayChain,
    *,
    verification: VerificationResult,
    acceptance: AcceptanceResult,
    promotion: PromotionDecision,
) -> None:
    """Validate that replayed outcome references identify the supplied objects."""
    if chain.verification_ref != verification.reference:
        raise ValueError("replay verification reference does not match result")
    if chain.acceptance_ref != acceptance.reference:
        raise ValueError("replay acceptance reference does not match result")
    if chain.promotion_ref != promotion.reference:
        raise ValueError("replay promotion reference does not match decision")
    validate_outcome_references(
        verification,
        acceptance,
        verification_ref=chain.verification_ref,
        acceptance_ref=chain.acceptance_ref,
    )
    if verification.reference not in acceptance.evidence:
        raise ValueError("acceptance does not carry the verification reference")
    if promotion.acceptance is None or promotion.acceptance.reference != acceptance.reference:
        raise ValueError("promotion does not carry the acceptance reference")


def audit_restored_chain(
    event_log_path: str | Path,
    snapshot: AttemptSnapshot,
    *,
    verification: VerificationResult | None = None,
    acceptance: AcceptanceResult | None = None,
    promotion: PromotionDecision | None = None,
    protocol_version: str | None = None,
    schema_version: int = EVENT_SCHEMA_VERSION,
    configuration_digest: str | None = None,
    budget_digest: str | None = None,
    treatment: str | None = None,
    capability_digest: str | None = None,
) -> RestoredChainAudit:
    """Audit a restored attempt without rerunning any execution stage."""
    log = EventLog(event_log_path, run_id=snapshot.manifest.attempt_id)
    events = log.read()
    protocols = {str(event.data["protocol_version"]) for event in events if event.data.get("protocol_version") is not None}
    schemas = {int(event.data["schema_version"]) for event in events if event.data.get("schema_version") is not None}
    if len(protocols) > 1 or len(schemas) > 1:
        raise ValueError("restored event log contains incompatible protocol or schema versions")
    observed_protocol = next(iter(protocols), None)
    observed_schema = next(iter(schemas), None)
    def observed_identity(name: str) -> str | None:
        values = {str(event.data[name]) for event in events if event.data.get(name) is not None}
        if len(values) > 1:
            raise ValueError(f"restored event log contains inconsistent {name}")
        return next(iter(values), None)
    observed_configuration = observed_identity("configuration_digest")
    observed_budget = observed_identity("budget_digest")
    observed_treatment = observed_identity("treatment")
    observed_capability = observed_identity("capability_digest")
    if protocol_version is not None:
        if observed_protocol != protocol_version:
            raise ValueError("restored event log protocol_version does not match expected protocol")
        if observed_schema != schema_version:
            raise ValueError("restored event log schema_version does not match expected schema")
        for name, expected, observed in (
            ("configuration_digest", configuration_digest, observed_configuration),
            ("budget_digest", budget_digest, observed_budget),
            ("treatment", treatment, observed_treatment),
            ("capability_digest", capability_digest, observed_capability),
        ):
            if expected is not None and observed != expected:
                raise ValueError(f"restored event log {name} does not match expected identity")
    replay = replay_events(events, run_id=snapshot.manifest.attempt_id)
    validate_replay_against_manifest(snapshot.manifest, replay)
    chain = replay_chain(events, run_id=snapshot.manifest.attempt_id)
    available = {str(path) for path in snapshot.artifact_paths}
    available.update(snapshot.manifest.artifact_refs)
    if verification is not None:
        available.add(verification.reference)
    if acceptance is not None:
        available.add(acceptance.reference)
    if promotion is not None:
        available.add(promotion.reference)
    references = classify_chain_references(chain, available_refs=available)
    integrity = assess_chain_integrity(chain, references)
    if verification is not None and acceptance is not None and promotion is not None:
        validate_outcome_chain(chain, verification=verification, acceptance=acceptance, promotion=promotion)
    if snapshot.manifest.budget_ledger is not None and replay.budget_ledger != snapshot.manifest.budget_ledger:
        raise ValueError("replayed budget ledger does not match attempt manifest")
    validate_attempt_lineage_chain(snapshot, chain, replay)
    return RestoredChainAudit(chain, replay, references, integrity, observed_protocol, observed_schema, observed_configuration, observed_budget, observed_treatment, observed_capability, decide_resume(chain, replay), replay.budget_ledger)


def validate_attempt_lineage_chain(snapshot: AttemptSnapshot, chain: ReplayChain, replay: ReplayState) -> None:
    """Require persisted event references to agree with attempt lineage facts."""
    lineage = snapshot.retry_lineage or snapshot.recovery_lineage
    if lineage is None:
        return
    expected_execution = f"execution://{snapshot.manifest.attempt_id}"
    if chain.execution_ref != expected_execution:
        raise ValueError("attempt lineage execution reference does not match manifest attempt")
    recovery_lineage = snapshot.recovery_lineage
    if recovery_lineage is not None:
        if chain.recovery_ref != recovery_lineage.recovery_reference:
            raise ValueError("attempt lineage recovery reference does not match recovery lineage")
        if replay.recovery_source_attempt_id != recovery_lineage.source_attempt_id:
            raise ValueError("replayed recovery source does not match recovery lineage")
    if snapshot.manifest.budget_ledger is not None and replay.budget_ledger != snapshot.manifest.budget_ledger:
        raise ValueError("attempt lineage budget ledger does not match replay")


def append_promotion_decision(
    log: EventLog,
    decision: PromotionDecision,
    *,
    verification_ref: str,
    timestamp: str,
) -> bool:
    """Persist promotion only after the same log contains verification and acceptance."""
    if not verification_ref.strip():
        raise ValueError("verification reference must be non-empty")
    if decision.acceptance is None:
        raise ValueError("promotion decision requires persisted acceptance")
    chain = replay_chain(log.read(), run_id=log.run_id)
    if chain.verification_ref != verification_ref:
        raise ValueError("promotion verification reference does not match event log")
    if chain.acceptance_ref != decision.acceptance.reference:
        raise ValueError("promotion acceptance does not match event log")
    return log.append_stage(
        timestamp=timestamp,
        event_type=EventType.EVIDENCE_ADDED,
        stage="promotion",
        ref=decision.reference,
        data={"promotion_status": decision.status.value, "authority_id": decision.authority_id},
    )


def append_recovery_plan(log: EventLog, plan: RecoveryPlan, execution_ref: str, timestamp: str) -> bool:
    """Persist recovery only when causally bound to the recorded execution."""
    if not plan.source_attempt_id.strip():
        raise ValueError("recovery plan source attempt must be non-empty")
    if execution_ref != f"execution://{plan.source_attempt_id}":
        raise ValueError("recovery plan source attempt does not match execution reference")
    chain = replay_chain(log.read(), run_id=log.run_id)
    if chain.execution_ref != execution_ref:
        raise ValueError("recovery requires a matching persisted execution stage")
    return log.append_stage(
        timestamp=timestamp,
        event_type=EventType.REPLAN,
        stage="recovery",
        ref=plan.reference,
        data={"source_attempt_id": plan.source_attempt_id, "recovery_action": plan.action.value},
    )
