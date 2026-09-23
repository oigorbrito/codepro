"""Per-run provenance contract binding raw evidence to a frozen study design."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping


SCHEMA_VERSION = 1
FREEZE_SCHEMA_VERSION = 1
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _required(name: str, value: str, issues: list[str]) -> None:
    if not value.strip():
        issues.append(f"{name} must be non-empty")


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    study_spec_hash: str
    study_spec_ref: str
    arkx_commit: str
    task_ref: str
    configuration_ref: str
    repetition_index: int
    executor_id: str
    executor_version: str
    environment_ref: str
    execution_record_ref: str
    execution_record_hash: str
    protocol_deviations: tuple[str, ...]
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "study_spec_hash": self.study_spec_hash,
            "study_spec_ref": self.study_spec_ref,
            "arkx_commit": self.arkx_commit,
            "task_ref": self.task_ref,
            "configuration_ref": self.configuration_ref,
            "repetition_index": self.repetition_index,
            "executor_id": self.executor_id,
            "executor_version": self.executor_version,
            "environment_ref": self.environment_ref,
            "execution_record_ref": self.execution_record_ref,
            "execution_record_hash": self.execution_record_hash,
            "protocol_deviations": list(self.protocol_deviations),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RunManifest":
        schema_version = int(value.get("schema_version", 0))
        if schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported run manifest schema: {schema_version}")
        return cls(
            run_id=str(value["run_id"]),
            study_spec_hash=str(value["study_spec_hash"]),
            study_spec_ref=str(value["study_spec_ref"]),
            arkx_commit=str(value["arkx_commit"]),
            task_ref=str(value["task_ref"]),
            configuration_ref=str(value["configuration_ref"]),
            repetition_index=int(value["repetition_index"]),
            executor_id=str(value["executor_id"]),
            executor_version=str(value["executor_version"]),
            environment_ref=str(value["environment_ref"]),
            execution_record_ref=str(value["execution_record_ref"]),
            execution_record_hash=str(value["execution_record_hash"]),
            protocol_deviations=tuple(value["protocol_deviations"]),
            schema_version=schema_version,
        )

    @classmethod
    def from_json(cls, value: str) -> "RunManifest":
        return cls.from_dict(json.loads(value))


@dataclass(frozen=True)
class FrozenRunManifest:
    run_manifest: RunManifest
    content_hash: str
    freeze_schema_version: int = FREEZE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "freeze_schema_version": self.freeze_schema_version,
            "content_hash": self.content_hash,
            "run_manifest": self.run_manifest.to_dict(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def validate_run_manifest(manifest: RunManifest) -> tuple[str, ...]:
    issues: list[str] = []
    for name in (
        "run_id",
        "study_spec_ref",
        "task_ref",
        "configuration_ref",
        "executor_id",
        "executor_version",
        "environment_ref",
        "execution_record_ref",
    ):
        _required(name, str(getattr(manifest, name)), issues)

    if not _SHA256_RE.fullmatch(manifest.study_spec_hash):
        issues.append("study_spec_hash must be a canonical sha256 reference")
    if not _GIT_SHA_RE.fullmatch(manifest.arkx_commit):
        issues.append("arkx_commit must be a full 40-character git SHA")
    if not _SHA256_RE.fullmatch(manifest.execution_record_hash):
        issues.append("execution_record_hash must be a canonical sha256 reference")
    if manifest.repetition_index < 1:
        issues.append("repetition_index must be at least 1")
    if any(not item.strip() for item in manifest.protocol_deviations):
        issues.append("protocol_deviations cannot contain blank entries")

    return tuple(sorted(set(issues)))


def freeze_run_manifest(manifest: RunManifest) -> FrozenRunManifest:
    """Validate and content-address one raw-run provenance record."""

    issues = validate_run_manifest(manifest)
    if issues:
        raise ValueError("Invalid run manifest: " + "; ".join(issues))
    digest = hashlib.sha256(manifest.to_json().encode("utf-8")).hexdigest()
    return FrozenRunManifest(run_manifest=manifest, content_hash=f"sha256:{digest}")


def hash_execution_record(raw_json: str) -> str:
    """Hash exact raw execution-record bytes after UTF-8 normalization by caller."""

    digest = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
