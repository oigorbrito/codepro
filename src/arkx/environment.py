"""Versioned execution-environment manifest for empirical Arkx runs."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping


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
        return cls(repository=str(value["repository"]), commit_sha=str(value["commit_sha"]))


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
        schema_version = int(value.get("schema_version", 0))
        if schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported environment manifest schema: {schema_version}")
        return cls(
            environment_id=str(value["environment_id"]),
            operating_system=str(value["operating_system"]),
            operating_system_version=str(value["operating_system_version"]),
            runner_image=str(value["runner_image"]),
            runner_image_version=str(value["runner_image_version"]),
            architecture=str(value["architecture"]),
            python_implementation=str(value["python_implementation"]),
            python_version=str(value["python_version"]),
            locale=str(value["locale"]),
            timezone=str(value["timezone"]),
            dependency_lock_ref=value.get("dependency_lock_ref"),
            dependency_lock_hash=value.get("dependency_lock_hash"),
            dependency_lock_justification=value.get("dependency_lock_justification"),
            container_image_digest=value.get("container_image_digest"),
            non_container_justification=value.get("non_container_justification"),
            action_pins=tuple(ActionPin.from_dict(item) for item in value.get("action_pins", ())),
            hermetic=bool(value["hermetic"]),
            nonhermetic_reasons=tuple(value.get("nonhermetic_reasons", ())),
            network_policy=str(value["network_policy"]),
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
