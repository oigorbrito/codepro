"""Deterministic progress and stagnation assessment for P2.

P2 observes snapshots. It never controls execution, selects an executor, or
turns an assessment into an acceptance status.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
import json
from time import perf_counter_ns
from typing import Any


SCHEMA_VERSION = 1


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class ProgressStatus(_ValueEnum):
    PROGRESS_PROVEN = "PROGRESS_PROVEN"
    PROGRESS_NOT_PROVEN = "PROGRESS_NOT_PROVEN"
    NO_PROGRESS = "NO_PROGRESS"
    UNKNOWN = "UNKNOWN"


class Confidence(_ValueEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ReasonCode(_ValueEnum):
    NEW_RELEVANT_FILE = "NEW_RELEVANT_FILE"
    NEW_PASSING_TEST = "NEW_PASSING_TEST"
    FAILURE_EXPLAINED = "FAILURE_EXPLAINED"
    ACCEPTANCE_DISTANCE_REDUCED = "ACCEPTANCE_DISTANCE_REDUCED"
    DIFF_DISTANCE_CHANGED = "DIFF_DISTANCE_CHANGED"
    REPEATED_ACTION = "REPEATED_ACTION"
    REPEATED_FAILURE_SIGNATURE = "REPEATED_FAILURE_SIGNATURE"
    NO_NEW_EVIDENCE = "NO_NEW_EVIDENCE"
    INSUFFICIENT_MEASUREMENT = "INSUFFICIENT_MEASUREMENT"
    CONTRADICTORY_SIGNALS = "CONTRADICTORY_SIGNALS"


@dataclass(frozen=True)
class ProgressConfig:
    """Explicit fail-closed measurement requirements."""

    required_fields: tuple[str, ...] = (
        "useful_files",
        "passing_tests",
        "explained_failures",
        "diff_distance",
        "acceptance_distance",
        "recent_actions",
        "failure_signatures",
    )


DEFAULT_CONFIG = ProgressConfig()


def _sorted_unique(values: tuple[str, ...] | None) -> list[str] | None:
    if values is None:
        return None
    return sorted(set(values))


@dataclass(frozen=True)
class ProgressSnapshot:
    useful_files: tuple[str, ...] | None = None
    passing_tests: tuple[str, ...] | None = None
    explained_failures: tuple[str, ...] | None = None
    diff_distance: int | None = None
    acceptance_distance: int | None = None
    recent_actions: tuple[str, ...] | None = None
    failure_signatures: tuple[str, ...] | None = None

    def normalized(self) -> "ProgressSnapshot":
        return replace(
            self,
            useful_files=None if self.useful_files is None else tuple(sorted(set(self.useful_files))),
            passing_tests=None if self.passing_tests is None else tuple(sorted(set(self.passing_tests))),
            explained_failures=None if self.explained_failures is None else tuple(sorted(set(self.explained_failures))),
            recent_actions=None if self.recent_actions is None else tuple(sorted(set(self.recent_actions))),
            failure_signatures=None if self.failure_signatures is None else tuple(sorted(set(self.failure_signatures))),
        )

    def to_dict(self) -> dict[str, Any]:
        value = self.normalized()
        return {
            "useful_files": _sorted_unique(value.useful_files),
            "passing_tests": _sorted_unique(value.passing_tests),
            "explained_failures": _sorted_unique(value.explained_failures),
            "diff_distance": value.diff_distance,
            "acceptance_distance": value.acceptance_distance,
            "recent_actions": _sorted_unique(value.recent_actions),
            "failure_signatures": _sorted_unique(value.failure_signatures),
        }


@dataclass(frozen=True)
class ProgressEvidence:
    useful_files_discovered: tuple[str, ...] | None
    tests_passed: tuple[str, ...] | None
    failures_explained: tuple[str, ...] | None
    diff_distance: int | None
    acceptance_distance: int | None
    repeated_actions: int | None
    failure_signatures: tuple[str, ...] | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "useful_files_discovered": _sorted_unique(self.useful_files_discovered),
            "tests_passed": _sorted_unique(self.tests_passed),
            "failures_explained": _sorted_unique(self.failures_explained),
            "diff_distance": self.diff_distance,
            "acceptance_distance": self.acceptance_distance,
            "repeated_actions": self.repeated_actions,
            "failure_signatures": _sorted_unique(self.failure_signatures),
        }


@dataclass(frozen=True)
class ProgressAssessment:
    schema_version: int
    status: ProgressStatus
    confidence: Confidence
    signals: tuple[str, ...]
    reason_codes: tuple[ReasonCode, ...]
    previous_snapshot: dict[str, Any] | None
    current_snapshot: dict[str, Any]
    evidence: ProgressEvidence
    telemetry: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "status": self.status.value,
            "confidence": self.confidence.value,
            "signals": list(self.signals),
            "reason_codes": [code.value for code in self.reason_codes],
            "previous_snapshot": self.previous_snapshot,
            "current_snapshot": self.current_snapshot,
            "evidence": self.evidence.to_dict(),
            "telemetry": self.telemetry,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _missing(snapshot: ProgressSnapshot, config: ProgressConfig) -> bool:
    values = snapshot.to_dict()
    return any(values.get(field) is None for field in config.required_fields)


def _contradictory(previous: ProgressSnapshot, current: ProgressSnapshot) -> bool:
    distances = (previous.diff_distance, previous.acceptance_distance, current.diff_distance, current.acceptance_distance)
    return any(isinstance(value, bool) or (value is not None and value < 0) for value in distances)


def assess_progress(
    previous: ProgressSnapshot | None,
    current: ProgressSnapshot,
    *,
    config: ProgressConfig = DEFAULT_CONFIG,
    assessment_duration_ms: int | None = None,
) -> ProgressAssessment:
    """Compare explicit snapshots without making any execution decision."""

    current = current.normalized()
    previous = None if previous is None else previous.normalized()
    reason_codes: list[ReasonCode] = []

    if previous is None or _missing(current, config) or _missing(previous, config):
        reason_codes.append(ReasonCode.INSUFFICIENT_MEASUREMENT)
        status = ProgressStatus.UNKNOWN
        confidence = Confidence.LOW
        evidence = ProgressEvidence(
            useful_files_discovered=current.useful_files,
            tests_passed=current.passing_tests,
            failures_explained=current.explained_failures,
            diff_distance=current.diff_distance,
            acceptance_distance=current.acceptance_distance,
            repeated_actions=None,
            failure_signatures=current.failure_signatures,
        )
        return _assessment(
            status=status,
            confidence=confidence,
            reason_codes=reason_codes,
            previous=previous,
            current=current,
            evidence=evidence,
            duration_ms=assessment_duration_ms,
        )

    if _contradictory(previous, current):
        reason_codes.append(ReasonCode.CONTRADICTORY_SIGNALS)
        evidence = ProgressEvidence(
            useful_files_discovered=current.useful_files,
            tests_passed=current.passing_tests,
            failures_explained=current.explained_failures,
            diff_distance=current.diff_distance,
            acceptance_distance=current.acceptance_distance,
            repeated_actions=0,
            failure_signatures=current.failure_signatures,
        )
        return _assessment(
            status=ProgressStatus.UNKNOWN,
            confidence=Confidence.LOW,
            reason_codes=reason_codes,
            previous=previous,
            current=current,
            evidence=evidence,
            duration_ms=assessment_duration_ms,
        )

    previous_files = set(previous.useful_files or ())
    current_files = set(current.useful_files or ())
    previous_tests = set(previous.passing_tests or ())
    current_tests = set(current.passing_tests or ())
    previous_explained = set(previous.explained_failures or ())
    current_explained = set(current.explained_failures or ())
    previous_failures = set(previous.failure_signatures or ())
    current_failures = set(current.failure_signatures or ())
    previous_actions = set(previous.recent_actions or ())
    current_actions = set(current.recent_actions or ())

    new_files = current_files - previous_files
    new_tests = current_tests - previous_tests
    new_explained = current_explained - previous_explained
    acceptance_reduced = current.acceptance_distance < previous.acceptance_distance
    diff_changed = current.diff_distance != previous.diff_distance
    diff_reduced = current.diff_distance < previous.diff_distance
    repeated_actions = len(previous_actions & current_actions)
    repeated_failure = bool(previous_failures & current_failures)
    new_failure = bool(current_failures - previous_failures)
    new_evidence = bool(new_files or new_tests or new_explained or acceptance_reduced or diff_reduced)

    if new_files:
        reason_codes.append(ReasonCode.NEW_RELEVANT_FILE)
    if new_tests:
        reason_codes.append(ReasonCode.NEW_PASSING_TEST)
    if new_explained:
        reason_codes.append(ReasonCode.FAILURE_EXPLAINED)
    if acceptance_reduced:
        reason_codes.append(ReasonCode.ACCEPTANCE_DISTANCE_REDUCED)
    if diff_changed:
        reason_codes.append(ReasonCode.DIFF_DISTANCE_CHANGED)
    if repeated_actions:
        reason_codes.append(ReasonCode.REPEATED_ACTION)
    if repeated_failure:
        reason_codes.append(ReasonCode.REPEATED_FAILURE_SIGNATURE)
    if not new_evidence:
        reason_codes.append(ReasonCode.NO_NEW_EVIDENCE)

    if new_evidence:
        status = ProgressStatus.PROGRESS_PROVEN
        confidence = Confidence.HIGH if (new_tests or acceptance_reduced) else Confidence.MEDIUM
    elif repeated_failure and not new_evidence:
        status = ProgressStatus.NO_PROGRESS
        confidence = Confidence.HIGH
    elif repeated_actions and current.acceptance_distance == previous.acceptance_distance:
        status = ProgressStatus.NO_PROGRESS
        confidence = Confidence.HIGH
    else:
        status = ProgressStatus.PROGRESS_NOT_PROVEN
        confidence = Confidence.MEDIUM if new_failure else Confidence.LOW

    evidence = ProgressEvidence(
        useful_files_discovered=current.useful_files,
        tests_passed=current.passing_tests,
        failures_explained=current.explained_failures,
        diff_distance=current.diff_distance,
        acceptance_distance=current.acceptance_distance,
        repeated_actions=repeated_actions,
        failure_signatures=current.failure_signatures,
    )
    return _assessment(
        status=status,
        confidence=confidence,
        reason_codes=reason_codes,
        previous=previous,
        current=current,
        evidence=evidence,
        duration_ms=assessment_duration_ms,
    )


def _assessment(
    *,
    status: ProgressStatus,
    confidence: Confidence,
    reason_codes: list[ReasonCode],
    previous: ProgressSnapshot | None,
    current: ProgressSnapshot,
    evidence: ProgressEvidence,
    duration_ms: int | None,
) -> ProgressAssessment:
    codes = tuple(dict.fromkeys(reason_codes))
    telemetry = {
        "progress_status": status.value,
        "progress_confidence": confidence.value,
        "progress_signal_count": len(codes),
        "repeated_action_count": evidence.repeated_actions,
        "failure_signature_count": None if current.failure_signatures is None else len(current.failure_signatures),
        "assessment_duration_ms": duration_ms,
    }
    return ProgressAssessment(
        schema_version=SCHEMA_VERSION,
        status=status,
        confidence=confidence,
        signals=[code.value for code in codes],
        reason_codes=codes,
        previous_snapshot=None if previous is None else previous.to_dict(),
        current_snapshot=current.to_dict(),
        evidence=evidence,
        telemetry=telemetry,
    )


def assess_progress_timed(
    previous: ProgressSnapshot | None,
    current: ProgressSnapshot,
    *,
    config: ProgressConfig = DEFAULT_CONFIG,
) -> ProgressAssessment:
    """Measure local assessment overhead; no action is taken."""

    started = perf_counter_ns()
    result = assess_progress(previous, current, config=config)
    duration_ms = max(0, (perf_counter_ns() - started) // 1_000_000)
    return replace(result, telemetry={**result.telemetry, "assessment_duration_ms": duration_ms})

