"""Evidence-bound attribution of run failures, blockers, and invalid observations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping


def _required_string(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _strict_bool(name: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be boolean")
    return value


SCHEMA_VERSION = 1
FREEZE_SCHEMA_VERSION = 1


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class IssueDisposition(_ValueEnum):
    SYSTEM_FAILURE = "SYSTEM_FAILURE"
    EXTERNAL_BLOCKER = "EXTERNAL_BLOCKER"
    INVALID_RUN = "INVALID_RUN"
    UNKNOWN = "UNKNOWN"


class AttributionDomain(_ValueEnum):
    SYSTEM_UNDER_TEST = "SYSTEM_UNDER_TEST"
    HARNESS = "HARNESS"
    VERIFIER = "VERIFIER"
    PROVIDER = "PROVIDER"
    ENVIRONMENT = "ENVIRONMENT"
    WORKLOAD = "WORKLOAD"
    CONFIGURATION = "CONFIGURATION"
    UNKNOWN = "UNKNOWN"


_EXTERNAL_DOMAINS = {
    AttributionDomain.HARNESS,
    AttributionDomain.VERIFIER,
    AttributionDomain.PROVIDER,
    AttributionDomain.ENVIRONMENT,
    AttributionDomain.WORKLOAD,
    AttributionDomain.CONFIGURATION,
}


@dataclass(frozen=True)
class RunIssueAttribution:
    attribution_id: str
    run_id: str
    disposition: IssueDisposition
    domain: AttributionDomain
    observed_signature: str
    attribution_basis: str
    evidence_refs: tuple[str, ...]
    retryability: str
    affects_primary_analysis: bool
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "attribution_id": self.attribution_id,
            "run_id": self.run_id,
            "disposition": self.disposition.value,
            "domain": self.domain.value,
            "observed_signature": self.observed_signature,
            "attribution_basis": self.attribution_basis,
            "evidence_refs": sorted(set(self.evidence_refs)),
            "retryability": self.retryability,
            "affects_primary_analysis": self.affects_primary_analysis,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RunIssueAttribution":
        if not isinstance(value, Mapping):
            raise ValueError("attribution payload must be a mapping")
        schema_version = value.get("schema_version", 0)
        if isinstance(schema_version, bool) or not isinstance(schema_version, int) or schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported attribution schema: {schema_version}")
        refs = value.get("evidence_refs", ())
        if not isinstance(refs, (list, tuple)):
            raise ValueError("evidence_refs must be a list or tuple")
        return cls(
            attribution_id=_required_string("attribution_id", value.get("attribution_id")),
            run_id=_required_string("run_id", value.get("run_id")),
            disposition=IssueDisposition(value["disposition"]),
            domain=AttributionDomain(value["domain"]),
            observed_signature=_required_string("observed_signature", value.get("observed_signature")),
            attribution_basis=_required_string("attribution_basis", value.get("attribution_basis")),
            evidence_refs=tuple(refs),
            retryability=_required_string("retryability", value.get("retryability")),
            affects_primary_analysis=_strict_bool("affects_primary_analysis", value.get("affects_primary_analysis")),
            schema_version=schema_version,
        )


@dataclass(frozen=True)
class FrozenRunIssueAttribution:
    attribution: RunIssueAttribution
    content_hash: str
    freeze_schema_version: int = FREEZE_SCHEMA_VERSION

    def to_json(self) -> str:
        value = {
            "freeze_schema_version": self.freeze_schema_version,
            "content_hash": self.content_hash,
            "attribution": self.attribution.to_dict(),
        }
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def validate_run_issue_attribution(value: RunIssueAttribution) -> tuple[str, ...]:
    issues: list[str] = []
    for name in (
        "attribution_id",
        "run_id",
        "observed_signature",
        "attribution_basis",
        "retryability",
    ):
        if not str(getattr(value, name)).strip():
            issues.append(f"{name} must be non-empty")

    if not value.evidence_refs:
        issues.append("attribution requires at least one evidence reference")
    elif any(not isinstance(ref, str) or not ref.strip() for ref in value.evidence_refs):
        issues.append("attribution evidence references must be non-blank strings")

    if value.domain is AttributionDomain.UNKNOWN and value.disposition is not IssueDisposition.UNKNOWN:
        issues.append("UNKNOWN domain must remain UNKNOWN disposition until evidence supports attribution")
    if value.disposition is IssueDisposition.UNKNOWN and value.domain is not AttributionDomain.UNKNOWN:
        issues.append("UNKNOWN disposition must use UNKNOWN domain")

    if value.disposition is IssueDisposition.SYSTEM_FAILURE and value.domain is not AttributionDomain.SYSTEM_UNDER_TEST:
        issues.append("SYSTEM_FAILURE may only be attributed to SYSTEM_UNDER_TEST")
    if value.disposition is IssueDisposition.EXTERNAL_BLOCKER and value.domain not in _EXTERNAL_DOMAINS:
        issues.append("EXTERNAL_BLOCKER must name a non-system external domain")
    if value.domain is AttributionDomain.SYSTEM_UNDER_TEST and value.disposition is IssueDisposition.EXTERNAL_BLOCKER:
        issues.append("SYSTEM_UNDER_TEST cannot be relabeled as an external blocker")

    return tuple(sorted(set(issues)))


def freeze_run_issue_attribution(value: RunIssueAttribution) -> FrozenRunIssueAttribution:
    issues = validate_run_issue_attribution(value)
    if issues:
        raise ValueError("Invalid run issue attribution: " + "; ".join(issues))
    digest = hashlib.sha256(value.to_json().encode("utf-8")).hexdigest()
    return FrozenRunIssueAttribution(attribution=value, content_hash=f"sha256:{digest}")
