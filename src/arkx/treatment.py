"""Frozen treatment/executor/model configuration for empirical CodePro studies."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import re
from typing import Any, Mapping


SCHEMA_VERSION = 1
FREEZE_SCHEMA_VERSION = 1
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _strict_schema(value: Mapping[str, Any]) -> int:
    raw = value.get("schema_version", 0)
    if isinstance(raw, bool) or not isinstance(raw, int) or raw != SCHEMA_VERSION:
        raise ValueError(f"Unsupported treatment configuration schema: {raw}")
    return raw


def _required_string(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _optional_string(name: str, value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string when present")
    return value


def _strict_int(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    return value


def _optional_int(name: str, value: Any) -> int | None:
    if value is None:
        return None
    return _strict_int(name, value)


def _string_tuple(name: str, value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{name} must be a list or tuple")
    if any(not isinstance(item, str) for item in value):
        raise ValueError(f"{name} must contain only strings")
    return tuple(value)


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class FallbackPolicy(_ValueEnum):
    DISABLED = "DISABLED"
    FROZEN_EXPLICIT = "FROZEN_EXPLICIT"


class SeedSupport(_ValueEnum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class TreatmentConfiguration:
    configuration_id: str
    executor_id: str
    executor_version: str
    provider_id: str | None
    model_id: str | None
    model_revision: str | None
    model_revision_justification: str | None
    prompt_ref: str
    prompt_hash: str
    tool_surface_ref: str
    tool_surface_hash: str
    provider_routing_ref: str
    parameters: Mapping[str, Any] = field(default_factory=dict)
    max_attempts: int = 1
    timeout_seconds: int = 1
    fallback_policy: FallbackPolicy = FallbackPolicy.DISABLED
    fallback_targets: tuple[str, ...] = ()
    seed_support: SeedSupport = SeedSupport.NOT_APPLICABLE
    seed: int | None = None
    seed_justification: str | None = None
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "configuration_id": self.configuration_id,
            "executor_id": self.executor_id,
            "executor_version": self.executor_version,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "model_revision": self.model_revision,
            "model_revision_justification": self.model_revision_justification,
            "prompt_ref": self.prompt_ref,
            "prompt_hash": self.prompt_hash,
            "tool_surface_ref": self.tool_surface_ref,
            "tool_surface_hash": self.tool_surface_hash,
            "provider_routing_ref": self.provider_routing_ref,
            "parameters": dict(self.parameters),
            "max_attempts": self.max_attempts,
            "timeout_seconds": self.timeout_seconds,
            "fallback_policy": self.fallback_policy.value,
            "fallback_targets": sorted(set(self.fallback_targets)),
            "seed_support": self.seed_support.value,
            "seed": self.seed,
            "seed_justification": self.seed_justification,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "TreatmentConfiguration":
        if not isinstance(value, Mapping):
            raise ValueError("treatment configuration payload must be a mapping")
        schema_version = _strict_schema(value)
        parameters = value.get("parameters", {})
        if not isinstance(parameters, Mapping):
            raise ValueError("parameters must be a mapping")
        return cls(
            configuration_id=_required_string("configuration_id", value.get("configuration_id")),
            executor_id=_required_string("executor_id", value.get("executor_id")),
            executor_version=_required_string("executor_version", value.get("executor_version")),
            provider_id=_optional_string("provider_id", value.get("provider_id")),
            model_id=_optional_string("model_id", value.get("model_id")),
            model_revision=_optional_string("model_revision", value.get("model_revision")),
            model_revision_justification=_optional_string("model_revision_justification", value.get("model_revision_justification")),
            prompt_ref=_required_string("prompt_ref", value.get("prompt_ref")),
            prompt_hash=_required_string("prompt_hash", value.get("prompt_hash")),
            tool_surface_ref=_required_string("tool_surface_ref", value.get("tool_surface_ref")),
            tool_surface_hash=_required_string("tool_surface_hash", value.get("tool_surface_hash")),
            provider_routing_ref=_required_string("provider_routing_ref", value.get("provider_routing_ref")),
            parameters=dict(parameters),
            max_attempts=_strict_int("max_attempts", value.get("max_attempts", 1)),
            timeout_seconds=_strict_int("timeout_seconds", value.get("timeout_seconds", 1)),
            fallback_policy=FallbackPolicy(value.get("fallback_policy", FallbackPolicy.DISABLED.value)),
            fallback_targets=_string_tuple("fallback_targets", value.get("fallback_targets", ())),
            seed_support=SeedSupport(value.get("seed_support", SeedSupport.NOT_APPLICABLE.value)),
            seed=_optional_int("seed", value.get("seed")),
            seed_justification=_optional_string("seed_justification", value.get("seed_justification")),
            schema_version=schema_version,
        )


@dataclass(frozen=True)
class FrozenTreatmentConfiguration:
    configuration: TreatmentConfiguration
    content_hash: str
    freeze_schema_version: int = FREEZE_SCHEMA_VERSION

    def to_json(self) -> str:
        value = {
            "freeze_schema_version": self.freeze_schema_version,
            "content_hash": self.content_hash,
            "configuration": self.configuration.to_dict(),
        }
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _required(name: str, value: str, issues: list[str]) -> None:
    if not value.strip():
        issues.append(f"{name} must be non-empty")


def validate_treatment_configuration(config: TreatmentConfiguration) -> tuple[str, ...]:
    issues: list[str] = []
    for name in (
        "configuration_id",
        "executor_id",
        "executor_version",
        "prompt_ref",
        "tool_surface_ref",
        "provider_routing_ref",
    ):
        _required(name, str(getattr(config, name)), issues)

    for name in ("prompt_hash", "tool_surface_hash"):
        if not _DIGEST_RE.fullmatch(str(getattr(config, name))):
            issues.append(f"{name} must be a canonical sha256 reference")

    if (config.provider_id is None) != (config.model_id is None):
        issues.append("provider_id and model_id must either both be declared or both be absent")
    if config.model_id is not None and config.model_revision is None:
        if not (config.model_revision_justification or "").strip():
            issues.append("missing model revision requires explicit justification")

    if config.max_attempts < 1:
        issues.append("max_attempts must be at least 1")
    if config.timeout_seconds < 1:
        issues.append("timeout_seconds must be at least 1")

    if config.fallback_policy is FallbackPolicy.DISABLED and config.fallback_targets:
        issues.append("DISABLED fallback policy cannot declare fallback_targets")
    if config.fallback_policy is FallbackPolicy.FROZEN_EXPLICIT and not config.fallback_targets:
        issues.append("FROZEN_EXPLICIT fallback policy requires frozen fallback_targets")

    if config.seed_support is SeedSupport.SUPPORTED:
        if config.seed is None:
            issues.append("SUPPORTED seed policy requires an explicit seed")
    else:
        if config.seed is not None:
            issues.append("unsupported/not-applicable seed policy cannot declare a seed")
        if not (config.seed_justification or "").strip():
            issues.append("unsupported/not-applicable seed policy requires justification")

    try:
        json.dumps(config.parameters, ensure_ascii=False, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError):
        issues.append("parameters must be finite JSON-serializable values")

    return tuple(sorted(set(issues)))


def freeze_treatment_configuration(config: TreatmentConfiguration) -> FrozenTreatmentConfiguration:
    issues = validate_treatment_configuration(config)
    if issues:
        raise ValueError("Invalid treatment configuration: " + "; ".join(issues))
    digest = hashlib.sha256(config.to_json().encode("utf-8")).hexdigest()
    return FrozenTreatmentConfiguration(configuration=config, content_hash=f"sha256:{digest}")
