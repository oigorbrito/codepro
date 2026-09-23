"""Versioned operational definitions for empirical Arkx metrics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping

from arkx.study import FrozenStudySpec, StudySpec, freeze_study_spec


SCHEMA_VERSION = 1
FREEZE_SCHEMA_VERSION = 1


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class MetricDataType(_ValueEnum):
    BOOLEAN = "BOOLEAN"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    CATEGORICAL = "CATEGORICAL"


class Direction(_ValueEnum):
    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"
    LOWER_IS_BETTER = "LOWER_IS_BETTER"
    NONE = "NONE"


@dataclass(frozen=True)
class MetricDefinition:
    metric_id: str
    data_type: MetricDataType
    unit: str
    direction: Direction
    source: str
    measurement_rule: str
    missing_semantics: str
    invalid_semantics: str
    precision_rule: str

    def to_dict(self) -> dict[str, str]:
        return {
            "metric_id": self.metric_id,
            "data_type": self.data_type.value,
            "unit": self.unit,
            "direction": self.direction.value,
            "source": self.source,
            "measurement_rule": self.measurement_rule,
            "missing_semantics": self.missing_semantics,
            "invalid_semantics": self.invalid_semantics,
            "precision_rule": self.precision_rule,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "MetricDefinition":
        return cls(
            metric_id=str(value["metric_id"]),
            data_type=MetricDataType(value["data_type"]),
            unit=str(value["unit"]),
            direction=Direction(value["direction"]),
            source=str(value["source"]),
            measurement_rule=str(value["measurement_rule"]),
            missing_semantics=str(value["missing_semantics"]),
            invalid_semantics=str(value["invalid_semantics"]),
            precision_rule=str(value["precision_rule"]),
        )


@dataclass(frozen=True)
class MeasurementContract:
    measurement_id: str
    metrics: tuple[MetricDefinition, ...]
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "measurement_id": self.measurement_id,
            "metrics": [
                metric.to_dict() for metric in sorted(self.metrics, key=lambda item: item.metric_id)
            ],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "MeasurementContract":
        schema_version = int(value.get("schema_version", 0))
        if schema_version != SCHEMA_VERSION:
            raise ValueError(f"Unsupported measurement contract schema: {schema_version}")
        return cls(
            measurement_id=str(value["measurement_id"]),
            metrics=tuple(MetricDefinition.from_dict(item) for item in value.get("metrics", ())),
            schema_version=schema_version,
        )


@dataclass(frozen=True)
class FrozenMeasurementContract:
    contract: MeasurementContract
    content_hash: str
    study_spec_hash: str
    freeze_schema_version: int = FREEZE_SCHEMA_VERSION

    def to_json(self) -> str:
        payload = {
            "freeze_schema_version": self.freeze_schema_version,
            "content_hash": self.content_hash,
            "study_spec_hash": self.study_spec_hash,
            "contract": self.contract.to_dict(),
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def validate_measurement_contract(contract: MeasurementContract) -> tuple[str, ...]:
    issues: list[str] = []
    if not contract.measurement_id.strip():
        issues.append("measurement_id must be non-empty")
    if not contract.metrics:
        issues.append("metrics must contain at least one operational definition")

    ids = [metric.metric_id for metric in contract.metrics]
    if len(set(ids)) != len(ids):
        issues.append("metric_id values must be unique")

    for metric in contract.metrics:
        for name in (
            "metric_id",
            "unit",
            "source",
            "measurement_rule",
            "missing_semantics",
            "invalid_semantics",
            "precision_rule",
        ):
            if not str(getattr(metric, name)).strip():
                issues.append(f"metric {metric.metric_id!r} requires non-empty {name}")
        if "zero" not in metric.missing_semantics.lower() and "null" not in metric.missing_semantics.lower() and "unknown" not in metric.missing_semantics.lower():
            issues.append(
                f"metric {metric.metric_id!r} missing_semantics must explicitly distinguish missing/unknown from observed values"
            )

    return tuple(sorted(set(issues)))


def validate_measurement_compatibility(
    contract: MeasurementContract, study: StudySpec
) -> tuple[str, ...]:
    issues = list(validate_measurement_contract(contract))
    defined = {metric.metric_id for metric in contract.metrics}
    missing = set(study.metrics) - defined
    if missing:
        issues.append(f"study metrics lack operational definitions: {sorted(missing)}")
    return tuple(sorted(set(issues)))


def freeze_measurement_contract(
    contract: MeasurementContract, study: FrozenStudySpec
) -> FrozenMeasurementContract:
    canonical = freeze_study_spec(study.study_spec)
    if canonical.content_hash != study.content_hash:
        raise ValueError("frozen Study Spec hash does not match Study Spec content")
    issues = validate_measurement_compatibility(contract, study.study_spec)
    if issues:
        raise ValueError("Invalid measurement contract: " + "; ".join(issues))
    identity = json.dumps(
        {"contract": contract.to_dict(), "study_spec_hash": study.content_hash},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return FrozenMeasurementContract(
        contract=contract,
        content_hash=f"sha256:{digest}",
        study_spec_hash=study.content_hash,
    )
