"""Executor-neutral adapter qualification and preflight contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any

from .harness import ErrorDomain, ErrorEnvelope, Retryability


class IntegrationKind(str, Enum):
    EXECUTOR = "EXECUTOR"
    PROVIDER = "PROVIDER"
    SANDBOX = "SANDBOX"
    EVALUATOR = "EVALUATOR"


class PreflightStatus(str, Enum):
    READY = "READY"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"
    FAILED = "FAILED"


class CapabilityProvenance(str, Enum):
    DECLARED = "DECLARED"
    OBSERVED = "OBSERVED"
    QUALIFIED = "QUALIFIED"


@dataclass(frozen=True)
class AdapterIdentity:
    kind: IntegrationKind
    name: str
    version: str | None = None
    configuration_digest: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("adapter name must be non-empty")

    def to_dict(self) -> dict[str, str | None]:
        return {"kind": self.kind.value, "name": self.name, "version": self.version, "configuration_digest": self.configuration_digest}


@dataclass(frozen=True)
class DependencyObservation:
    name: str
    available: bool | None
    version: str | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("dependency name must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "available": self.available, "version": self.version, "reason": self.reason}


@dataclass(frozen=True)
class AdapterPreflight:
    identity: AdapterIdentity
    status: PreflightStatus
    dependencies: tuple[DependencyObservation, ...] = ()
    capabilities: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    reason: str | None = None
    capability_digest: str | None = None
    capability_provenance: CapabilityProvenance = CapabilityProvenance.DECLARED

    def __post_init__(self) -> None:
        if any(not value.strip() for value in self.capabilities + self.evidence_refs):
            raise ValueError("preflight capabilities and evidence refs must be non-empty")
        if self.capability_provenance is CapabilityProvenance.QUALIFIED and not self.evidence_refs:
            raise ValueError("qualified capabilities require evidence references")
        object.__setattr__(self, "dependencies", tuple(sorted(self.dependencies, key=lambda item: item.name)))
        object.__setattr__(self, "capabilities", tuple(sorted(set(self.capabilities))))
        object.__setattr__(self, "evidence_refs", tuple(sorted(set(self.evidence_refs))))

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "status": self.status.value,
            "dependencies": [item.to_dict() for item in self.dependencies],
            "capabilities": list(self.capabilities),
            "evidence_refs": list(self.evidence_refs),
            "reason": self.reason,
            "capability_digest": self.capability_digest,
            "capability_provenance": self.capability_provenance.value,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @property
    def reference(self) -> str:
        digest = hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()[:16]
        return f"preflight://{digest}"


def preflight_error(preflight: AdapterPreflight) -> ErrorEnvelope | None:
    """Map non-ready preflight state without guessing retryability."""
    if preflight.status is PreflightStatus.READY:
        return None
    domains = {
        IntegrationKind.EXECUTOR: ErrorDomain.EXECUTOR,
        IntegrationKind.PROVIDER: ErrorDomain.PROVIDER,
        IntegrationKind.SANDBOX: ErrorDomain.SANDBOX,
        IntegrationKind.EVALUATOR: ErrorDomain.VERIFICATION,
    }
    code = f"PREFLIGHT_{preflight.status.value}"
    message = preflight.reason or f"adapter {preflight.identity.name} is not ready"
    return ErrorEnvelope(domains[preflight.identity.kind], code, message, Retryability.UNKNOWN, (preflight.reference,))


def provider_error_envelope(payload: Any, *, raw_evidence_refs: tuple[str, ...] = ()) -> ErrorEnvelope:
    """Normalize a provider error payload without importing a provider SDK."""
    if not isinstance(payload, dict) or not isinstance(payload.get("error"), dict):
        raise ValueError("provider payload must contain an error object")
    error = payload["error"]
    code = str(error.get("code", "UNKNOWN"))
    message = str(error.get("message", "provider returned an error"))
    return ErrorEnvelope(
        ErrorDomain.PROVIDER,
        f"PROVIDER_{code}",
        message,
        Retryability.UNKNOWN,
        raw_evidence_refs,
    )


def process_error_envelope(
    kind: IntegrationKind,
    *,
    returncode: int | None,
    message: str,
    raw_evidence_refs: tuple[str, ...] = (),
    attempt_number: int | None = None,
) -> ErrorEnvelope:
    """Normalize a process boundary failure while retaining its integration kind."""
    if kind not in (IntegrationKind.EXECUTOR, IntegrationKind.SANDBOX, IntegrationKind.EVALUATOR):
        raise ValueError("process failures require executor, sandbox, or evaluator kind")
    domains = {
        IntegrationKind.EXECUTOR: ErrorDomain.EXECUTOR,
        IntegrationKind.SANDBOX: ErrorDomain.SANDBOX,
        IntegrationKind.EVALUATOR: ErrorDomain.VERIFICATION,
    }
    suffix = "UNKNOWN" if returncode is None else str(returncode)
    return ErrorEnvelope(domains[kind], f"{kind.value}_PROCESS_{suffix}", message, Retryability.UNKNOWN, raw_evidence_refs, attempt_number)


def exception_error_envelope(
    kind: IntegrationKind,
    error: BaseException,
    *,
    raw_evidence_refs: tuple[str, ...] = (),
) -> ErrorEnvelope:
    """Normalize an adapter exception without inferring retryability."""
    domains = {
        IntegrationKind.EXECUTOR: ErrorDomain.EXECUTOR,
        IntegrationKind.PROVIDER: ErrorDomain.PROVIDER,
        IntegrationKind.SANDBOX: ErrorDomain.SANDBOX,
        IntegrationKind.EVALUATOR: ErrorDomain.VERIFICATION,
    }
    return ErrorEnvelope(
        domains[kind],
        f"{kind.value}_{type(error).__name__.upper()}",
        str(error) or type(error).__name__,
        Retryability.UNKNOWN,
        raw_evidence_refs,
    )


def assess_preflight(
    identity: AdapterIdentity,
    dependencies: tuple[DependencyObservation, ...],
    *,
    capabilities: tuple[str, ...] = (),
    evidence_refs: tuple[str, ...] = (),
    failure_reason: str | None = None,
    capability_digest: str | None = None,
    capability_provenance: CapabilityProvenance = CapabilityProvenance.DECLARED,
) -> AdapterPreflight:
    if failure_reason:
        status = PreflightStatus.FAILED
    elif any(item.available is False for item in dependencies):
        status = PreflightStatus.BLOCKED
    elif any(item.available is None for item in dependencies):
        status = PreflightStatus.UNKNOWN
    elif identity.version is None or identity.configuration_digest is None:
        status = PreflightStatus.UNKNOWN
    else:
        status = PreflightStatus.READY
    return AdapterPreflight(identity, status, dependencies, capabilities, evidence_refs, failure_reason, capability_digest, capability_provenance)
