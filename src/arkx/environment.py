"""Versioned execution-environment manifest for empirical Arkx runs."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping


def _schema_version(value: Mapping[str, Any]) -> int:
    raw = value.get("schema_version", 0)
    if isinstance(raw, bool) or not isinstance(raw, int) or raw != SCHEMA_VERSION:
        raise ValueError(f"Unsupported environment manifest schema: {raw}")
    return raw


def _strict_bool(name: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be boolean")
    return value


def _required_string(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


SCHEMA_VERSION = 1
FREEZE_SCHEMA_VERSION = 1
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


@dataclass(frozen=True)
class ActionPin:
    repository: str
    commit_sha: str

    def to_dict(self) -> dict[str, str]:
        return {"repository": self.repository, "commit_sha": self.commit_sha}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ActionPin":
        if not isinstance(value, Mapping):
            raise ValueError("action pin must be a mapping")
        return cls(
            repository=_required_string("repository", value.get("repository")),
            commit_sha=_required_string("commit_sha", value.get("commit_sha")),
        )


@dataclass(frozen=True)
class EnvironmentManifest:
    environment_id: str
    operating_system: str
    operating_system_version: str
    runner_image: str
    runner_image_version: str
    architecture: str
    python_implementation: str
    python_version: str
    locale: str
    timezone: str
    dependency_lock_ref: str | None
    dependency_lock_hash: str | None
    dependency_lock_justification: str | None
    container_image_digest: str | None
    non_container_justification: str | None
    action_pins: tuple[ActionPin, ...]
    hermetic: bool
    nonhermetic_reasons: tuple[str, ...]
    network_policy: str
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "environment_id": self.environment_id,
            "operating_system": self.operating_system,
            "operating_system_version": self.operating_system_version,
            "runner_image": self.runner_image,
            "runner_image_version": self.runner_image_version,
            "architecture": self.architecture,
            "python_implementation": self.python_implementation,
            "python_version": self.python_version,
            "locale": self.locale,
            "timezone": self.timezone,
            "dependency_lock_ref": self.dependency_lock_ref,
            "dependency_lock_hash": self.dependency_lock_hash,
            "dependency_lock_justification": self.dependency_lock_justification,
            "container_image_digest": self.container_image_digest,
            "non_container_justification": self.non_container_justification,
            "action_pins": [
                pin.to_dict() for pin in sorted(self.action_pins, key=lambda x: x.repository)
            ],
            "hermetic": self.hermetic,
            "nonhermetic_reasons": sorted(set(self.nonhermetic_reasons)),
            "network_policy": self.network_policy,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "EnvironmentManifest":
        if not isinstance(value, Mapping):
            raise ValueError("environment manifest must be a mapping")
        schema_version = _schema_version(value)
        pins = value.get("action_pins", ())
        reasons = value.get("nonhermetic_reasons", ())
        if not isinstance(pins, (list, tuple)):
            raise ValueError("action_pins must be a list or tuple")
        if not isinstance(reasons, (list, tuple)):
            raise ValueError("nonhermetic_reasons must be a list or tuple")
        return cls(
            environment_id=_required_string("environment_id", value.get("environment_id")),
            operating_system=_required_string("operating_system", value.get("operating_system")),
            operating_system_version=_required_string("operating_system_version", value.get("operating_system_version")),
            runner_image=_required_string("runner_image", value.get("runner_image")),
            runner_image_version=_required_string("runner_image_version", value.get("runner_image_version")),
            architecture=_required_string("architecture", value.get("architecture")),
            python_implementation=_required_string("python_implementation", value.get("python_implementation")),
            python_version=_required_string("python_version", value.get("python_version")),
            locale=_required_string("locale", value.get("locale")),
            timezone=_required_string("timezone", value.get("timezone")),
            dependency_lock_ref=value.get("dependency_lock_ref"),
            dependency_lock_hash=value.get("dependency_lock_hash"),
            dependency_lock_justification=value.get("dependency_lock_justification"),
            container_image_digest=value.get("container_image_digest"),
            non_container_justification=value.get("non_container_justification"),
            action_pins=tuple(ActionPin.from_dict(item) for item in pins),
            hermetic=_strict_bool("hermetic", value.get("hermetic")),
            nonhermetic_reasons=tuple(reasons),
            network_policy=_required_string("network_policy", value.get("network_policy")),
            schema_version=schema_version,
        )


@dataclass(frozen=True)
class FrozenEnvironmentManifest:
    environment: EnvironmentManifest
    content_hash: str
    freeze_schema_version: int = FREEZE_SCHEMA_VERSION

    def to_json(self) -> str:
        value = {
            "freeze_schema_version": self.freeze_schema_version,
            "content_hash": self.content_hash,
            "environment": self.environment.to_dict(),
        }
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _required(name: str, value: str, issues: list[str]) -> None:
    if not value.strip():
        issues.append(f"{name} must be non-empty")


def validate_environment_manifest(environment: EnvironmentManifest) -> tuple[str, ...]:
    issues: list[str] = []
    for name in (
        "environment_id",
        "operating_system",
        "operating_system_version",
        "runner_image",
        "runner_image_version",
        "architecture",
        "python_implementation",
        "python_version",
        "locale",
        "timezone",
        "network_policy",
    ):
        _required(name, str(getattr(environment, name)), issues)

    if any(not isinstance(item, str) or not item.strip() for item in environment.nonhermetic_reasons):
        issues.append("nonhermetic_reasons cannot contain blanks")

    if not environment.action_pins:
        issues.append("action_pins must contain every external CI action used by the environment")
    for pin in environment.action_pins:
        if not pin.repository.strip():
            issues.append("action pin repository must be non-empty")
        if not _SHA_RE.fullmatch(pin.commit_sha):
            issues.append("action pins must use full 40-character commit SHAs")

    if environment.dependency_lock_ref is None:
        if not (environment.dependency_lock_justification or "").strip():
            issues.append("missing dependency lock requires explicit justification")
        if environment.dependency_lock_hash is not None:
            issues.append("dependency_lock_hash requires dependency_lock_ref")
    else:
        if not (environment.dependency_lock_hash or ""):
            issues.append("dependency_lock_ref requires dependency_lock_hash")
        elif not _DIGEST_RE.fullmatch(environment.dependency_lock_hash or ""):
            issues.append("dependency_lock_hash must be a canonical sha256 reference")

    if environment.container_image_digest is None:
        if not (environment.non_container_justification or "").strip():
            issues.append("non-container execution requires explicit justification")
    elif not _DIGEST_RE.fullmatch(environment.container_image_digest):
        issues.append("container_image_digest must be a canonical sha256 reference")

    if environment.hermetic and environment.nonhermetic_reasons:
        issues.append("hermetic environment cannot declare nonhermetic_reasons")
    if not environment.hermetic and not environment.nonhermetic_reasons:
        issues.append("non-hermetic environment must declare residual drift reasons")

    return tuple(sorted(set(issues)))


def freeze_environment_manifest(environment: EnvironmentManifest) -> FrozenEnvironmentManifest:
    issues = validate_environment_manifest(environment)
    if issues:
        raise ValueError("Invalid environment manifest: " + "; ".join(issues))
    digest = hashlib.sha256(environment.to_json().encode("utf-8")).hexdigest()
    return FrozenEnvironmentManifest(environment=environment, content_hash=f"sha256:{digest}")
