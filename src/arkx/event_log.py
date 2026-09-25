"""Minimal CodePro v1 event-chain audit contract."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


class EventLogError(Exception):
    """Base error for event-log loading and interpretation failures."""


class EventLogFormatError(EventLogError):
    """The event-log file cannot be loaded or interpreted as v1 input."""


class EventLogIntegrityError(EventLogError):
    """A loaded event-log integrity operation cannot be completed."""


class ChainIntegrity(str, Enum):
    COMPLETE = "COMPLETE"
    EMPTY = "EMPTY"
    INVALID = "INVALID"
    TAMPERED = "TAMPERED"


@dataclass(frozen=True)
class EventRecord:
    sequence: int
    event_type: str
    payload: Mapping[str, Any]
    previous_digest: str | None
    digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "event_type": self.event_type,
            "payload": dict(self.payload),
            "previous_digest": self.previous_digest,
            "digest": self.digest,
        }


class _HashableEventList(list[dict[str, Any]]):
    """List-shaped serialized events that can cross the legacy consumer set."""

    def __hash__(self) -> int:
        encoded = json.dumps(self, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hash(encoded)


@dataclass(frozen=True)
class EventChain:
    events: tuple[EventRecord, ...] = ()
    integrity: ChainIntegrity = ChainIntegrity.EMPTY
    verification_ref: str | None = None
    acceptance_ref: str | None = None
    promotion_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "events": _HashableEventList(event.to_dict() for event in self.events),
            "event_count": len(self.events),
            "head_digest": self.events[-1].digest if self.events else None,
            "verification_ref": self.verification_ref,
            "acceptance_ref": self.acceptance_ref,
            "promotion_ref": self.promotion_ref,
        }


@dataclass(frozen=True)
class ReplayState:
    run_id: str


@dataclass(frozen=True)
class ReplayAudit:
    run_id: str
    protocol_version: str | None
    schema_version: str
    configuration_digest: str | None
    budget_digest: str | None
    treatment: str | None
    capability_digest: str | None
    integrity: ChainIntegrity
    chain: EventChain
    replay: ReplayState


def _canonical_event_value(event: Mapping[str, Any]) -> str:
    value = {
        "sequence": event["sequence"],
        "event_type": event["event_type"],
        "payload": event["payload"],
        "previous_digest": event["previous_digest"],
    }
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise EventLogFormatError("event payload is not strict JSON") from exc


def _digest(event: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_event_value(event).encode("utf-8")).hexdigest()


def _metadata(snapshot: Any) -> dict[str, Any]:
    manifest = getattr(snapshot, "manifest", snapshot)
    execution = getattr(snapshot, "execution", {})

    def value(name: str, default: Any = None) -> Any:
        if isinstance(manifest, Mapping):
            return manifest.get(name, default)
        return getattr(manifest, name, default)

    run_id = value("attempt_id", value("run_id"))
    if not isinstance(run_id, str) or not run_id.strip():
        raise EventLogFormatError("snapshot must provide a non-empty attempt_id")
    capability_digest = value("capability_digest")
    if capability_digest is None and isinstance(execution, Mapping):
        capability_digest = execution.get("capability_digest")
    return {
        "run_id": run_id,
        "protocol_version": value("protocol_version"),
        "schema_version": str(value("schema_version", 1)),
        "configuration_digest": value("configuration_digest"),
        "budget_digest": value("budget_digest"),
        "treatment": value("treatment"),
        "capability_digest": capability_digest,
    }


def _audit(metadata: Mapping[str, Any], chain: EventChain, integrity: ChainIntegrity) -> ReplayAudit:
    return ReplayAudit(
        run_id=metadata["run_id"],
        protocol_version=metadata["protocol_version"],
        schema_version=metadata["schema_version"],
        configuration_digest=metadata["configuration_digest"],
        budget_digest=metadata["budget_digest"],
        treatment=metadata["treatment"],
        capability_digest=metadata["capability_digest"],
        integrity=integrity,
        chain=EventChain(chain.events, integrity, chain.verification_ref, chain.acceptance_ref, chain.promotion_ref),
        replay=ReplayState(metadata["run_id"]),
    )


def _parse_event(raw: Any) -> EventRecord:
    if not isinstance(raw, Mapping):
        raise EventLogFormatError("event must be a mapping")
    required = {"sequence", "event_type", "payload", "previous_digest", "digest"}
    if not required.issubset(raw):
        raise EventLogFormatError("event schema is missing required fields")
    sequence = raw["sequence"]
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
        raise EventLogFormatError("event sequence must be a non-negative integer")
    event_type = raw["event_type"]
    if not isinstance(event_type, str) or not event_type.strip():
        raise EventLogFormatError("event_type must be a non-empty string")
    payload = raw["payload"]
    if not isinstance(payload, Mapping):
        raise EventLogFormatError("event payload must be a mapping")
    previous_digest = raw["previous_digest"]
    if previous_digest is not None and not isinstance(previous_digest, str):
        raise EventLogFormatError("previous_digest must be a string or null")
    digest = raw["digest"]
    if not isinstance(digest, str) or len(digest) != 64:
        raise EventLogFormatError("digest must be a SHA-256 hex string")
    try:
        int(digest, 16)
    except ValueError as exc:
        raise EventLogFormatError("digest must be a SHA-256 hex string") from exc
    return EventRecord(sequence, event_type, dict(payload), previous_digest, digest)


def audit_restored_chain(
    event_log_path: str | Path,
    snapshot: Any,
    outcomes: Any = None,
) -> ReplayAudit:
    """Load and fail-closed audit a v1 JSON-lines event chain."""

    del outcomes
    metadata = _metadata(snapshot)
    path = Path(event_log_path)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise EventLogFormatError(f"cannot load event log: {path}") from exc

    if not lines:
        return _audit(metadata, EventChain(), ChainIntegrity.EMPTY)

    events: list[EventRecord] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EventLogFormatError("event log contains invalid JSON") from exc
        events.append(_parse_event(raw))

    if not events:
        return _audit(metadata, EventChain(), ChainIntegrity.EMPTY)

    stage_refs: dict[str, str | None] = {"verification": None, "acceptance": None, "promotion": None}
    for expected, event in enumerate(events):
        if event.sequence != expected:
            return _audit(metadata, EventChain(tuple(events), ChainIntegrity.INVALID), ChainIntegrity.INVALID)
        if expected == 0:
            if event.previous_digest is not None:
                return _audit(metadata, EventChain(tuple(events), ChainIntegrity.TAMPERED), ChainIntegrity.TAMPERED)
        elif event.previous_digest != events[expected - 1].digest:
            return _audit(metadata, EventChain(tuple(events), ChainIntegrity.TAMPERED), ChainIntegrity.TAMPERED)
        if event.digest != _digest(event.to_dict()):
            return _audit(metadata, EventChain(tuple(events), ChainIntegrity.TAMPERED), ChainIntegrity.TAMPERED)

        stage = event.payload.get("stage")
        ref = event.payload.get("ref")
        if stage in stage_refs:
            if not isinstance(ref, str) or not ref.strip():
                return _audit(metadata, EventChain(tuple(events), ChainIntegrity.INVALID), ChainIntegrity.INVALID)
            if stage_refs[stage] is not None and stage_refs[stage] != ref:
                return _audit(metadata, EventChain(tuple(events), ChainIntegrity.INVALID), ChainIntegrity.INVALID)
            stage_refs[stage] = ref

    return _audit(metadata, EventChain(tuple(events), ChainIntegrity.COMPLETE, stage_refs["verification"], stage_refs["acceptance"], stage_refs["promotion"]), ChainIntegrity.COMPLETE)
