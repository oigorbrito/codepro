"""Deterministic, conservative task characterization for P1.

This module consumes explicit signals only. It does not inspect natural
language, invoke a model, select an executor, or perform routing.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
import json
from time import perf_counter_ns
from typing import Any, Mapping


SCHEMA_VERSION = 1


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class Scope(_ValueEnum):
    SIMPLE = "SIMPLE"
    LOCALIZED = "LOCALIZED"
    REPOSITORY_WIDE = "REPOSITORY_WIDE"
    UNKNOWN = "UNKNOWN"


class RecommendedPath(_ValueEnum):
    SIMPLE_PATH = "SIMPLE_PATH"
    LOCALIZED_PATH = "LOCALIZED_PATH"
    REPOSITORY_WIDE_PATH = "REPOSITORY_WIDE_PATH"
    QUALIFICATION_REQUIRED = "QUALIFICATION_REQUIRED"


class Confidence(_ValueEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class SignalLevel(_ValueEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class TestSurface(_ValueEnum):
    NONE = "NONE"
    LIMITED = "LIMITED"
    BROAD = "BROAD"
    UNKNOWN = "UNKNOWN"


class ReasonCode(_ValueEnum):
    SINGLE_FILE = "SINGLE_FILE"
    BOUNDED_FILE_SET = "BOUNDED_FILE_SET"
    MULTI_COMPONENT = "MULTI_COMPONENT"
    SINGLE_COMPONENT = "SINGLE_COMPONENT"
    LOW_DEPENDENCY_FANOUT = "LOW_DEPENDENCY_FANOUT"
    HIGH_DEPENDENCY_FANOUT = "HIGH_DEPENDENCY_FANOUT"
    BROAD_TEST_SURFACE = "BROAD_TEST_SURFACE"
    AMBIGUOUS_ACCEPTANCE = "AMBIGUOUS_ACCEPTANCE"
    RISK_MARKER = "RISK_MARKER"
    ARCHITECTURAL_CHANGE = "ARCHITECTURAL_CHANGE"
    SHARED_STATE = "SHARED_STATE"
    INSUFFICIENT_FILE_SIGNAL = "INSUFFICIENT_FILE_SIGNAL"
    INSUFFICIENT_COMPONENT_SIGNAL = "INSUFFICIENT_COMPONENT_SIGNAL"
    INSUFFICIENT_ACCEPTANCE_SIGNAL = "INSUFFICIENT_ACCEPTANCE_SIGNAL"
    CONTRADICTORY_SIGNALS = "CONTRADICTORY_SIGNALS"


@dataclass(frozen=True)
class CharacterizationConfig:
    """Centralized, reviewable thresholds for the initial heuristic."""

    max_simple_files: int = 1
    max_localized_files: int = 5
    max_localized_components: int = 2
    max_localized_fanout: int = 3
    max_simple_acceptance_checks: int = 1


DEFAULT_CONFIG = CharacterizationConfig()


def _sorted_unique(values: tuple[str, ...] | None) -> list[str] | None:
    if values is None:
        return None
    return sorted(set(values))


@dataclass(frozen=True)
class TaskSignals:
    """Explicit signals supplied by an upstream observer or fixture."""

    candidate_files: tuple[str, ...] | None = None
    dependency_edges: tuple[tuple[str, str], ...] | None = None
    affected_components: tuple[str, ...] | None = None
    known_tests: tuple[str, ...] | None = None
    ambiguity_markers: tuple[str, ...] | None = None
    risk_markers: tuple[str, ...] | None = None
    acceptance_checks: tuple[str, ...] | None = None
    state_shared: bool | None = None
    architectural_change: bool | None = None
    declared_scope: Scope | None = None

    def normalized(self) -> "TaskSignals":
        edges = None if self.dependency_edges is None else tuple(sorted(set(self.dependency_edges)))
        return replace(
            self,
            candidate_files=None if self.candidate_files is None else tuple(sorted(set(self.candidate_files))),
            dependency_edges=edges,
            affected_components=None if self.affected_components is None else tuple(sorted(set(self.affected_components))),
            known_tests=None if self.known_tests is None else tuple(sorted(set(self.known_tests))),
            ambiguity_markers=None if self.ambiguity_markers is None else tuple(sorted(set(self.ambiguity_markers))),
            risk_markers=None if self.risk_markers is None else tuple(sorted(set(self.risk_markers))),
            acceptance_checks=None if self.acceptance_checks is None else tuple(sorted(set(self.acceptance_checks))),
        )

    def to_dict(self) -> dict[str, Any]:
        value = self.normalized()
        return {
            "candidate_files": _sorted_unique(value.candidate_files),
            "dependency_edges": None if value.dependency_edges is None else [list(edge) for edge in value.dependency_edges],
            "affected_components": _sorted_unique(value.affected_components),
            "known_tests": _sorted_unique(value.known_tests),
            "ambiguity_markers": _sorted_unique(value.ambiguity_markers),
            "risk_markers": _sorted_unique(value.risk_markers),
            "acceptance_checks": _sorted_unique(value.acceptance_checks),
            "state_shared": value.state_shared,
            "architectural_change": value.architectural_change,
            "declared_scope": None if value.declared_scope is None else value.declared_scope.value,
        }


@dataclass(frozen=True)
class TaskCharacterization:
    schema_version: int
    scope: Scope
    estimated_files: int | None
    dependency_fanout: int | None
    test_surface: TestSurface
    ambiguity: SignalLevel
    risk: SignalLevel
    acceptance_complexity: SignalLevel
    confidence: Confidence
    signals: tuple[ReasonCode, ...]
    recommended_path: RecommendedPath
    input_signals: dict[str, Any]
    derived_signals: dict[str, Any]
    telemetry: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "scope": self.scope.value,
            "estimated_files": self.estimated_files,
            "dependency_fanout": self.dependency_fanout,
            "test_surface": self.test_surface.value,
            "ambiguity": self.ambiguity.value,
            "risk": self.risk.value,
            "acceptance_complexity": self.acceptance_complexity.value,
            "confidence": self.confidence.value,
            "signals": [signal.value for signal in self.signals],
            "recommended_path": self.recommended_path.value,
            "input_signals": self.input_signals,
            "derived_signals": self.derived_signals,
            "telemetry": self.telemetry,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _test_surface(known_tests: tuple[str, ...] | None) -> TestSurface:
    if known_tests is None:
        return TestSurface.UNKNOWN
    if not known_tests:
        return TestSurface.NONE
    return TestSurface.LIMITED if len(known_tests) <= 2 else TestSurface.BROAD


def _level_for_count(count: int | None, *, unknown: SignalLevel = SignalLevel.UNKNOWN) -> SignalLevel:
    if count is None:
        return unknown
    if count == 0:
        return SignalLevel.LOW
    if count <= 2:
        return SignalLevel.MEDIUM
    return SignalLevel.HIGH


def characterize(
    task_signals: TaskSignals,
    *,
    config: CharacterizationConfig = DEFAULT_CONFIG,
    characterization_duration_ms: int | None = None,
) -> TaskCharacterization:
    """Classify explicit signals conservatively and without side effects."""

    signals = task_signals.normalized()
    file_count = None if signals.candidate_files is None else len(signals.candidate_files)
    fanout = None if signals.dependency_edges is None else len(signals.dependency_edges)
    component_count = None if signals.affected_components is None else len(signals.affected_components)
    acceptance_count = None if signals.acceptance_checks is None else len(signals.acceptance_checks)
    ambiguity_count = None if signals.ambiguity_markers is None else len(signals.ambiguity_markers)
    risk_count = None if signals.risk_markers is None else len(signals.risk_markers)

    reason_codes: list[ReasonCode] = []
    if file_count == 1:
        reason_codes.append(ReasonCode.SINGLE_FILE)
    elif file_count is not None and file_count > 1:
        reason_codes.append(ReasonCode.BOUNDED_FILE_SET)
    if component_count == 1:
        reason_codes.append(ReasonCode.SINGLE_COMPONENT)
    elif component_count is not None and component_count > 1:
        reason_codes.append(ReasonCode.MULTI_COMPONENT)
    if fanout is not None and fanout <= config.max_localized_fanout:
        reason_codes.append(ReasonCode.LOW_DEPENDENCY_FANOUT)
    elif fanout is not None:
        reason_codes.append(ReasonCode.HIGH_DEPENDENCY_FANOUT)
    if signals.known_tests is not None and len(signals.known_tests) > 2:
        reason_codes.append(ReasonCode.BROAD_TEST_SURFACE)
    if ambiguity_count:
        reason_codes.append(ReasonCode.AMBIGUOUS_ACCEPTANCE)
    if risk_count:
        reason_codes.append(ReasonCode.RISK_MARKER)
    if signals.architectural_change:
        reason_codes.append(ReasonCode.ARCHITECTURAL_CHANGE)
    if signals.state_shared:
        reason_codes.append(ReasonCode.SHARED_STATE)

    incomplete = (
        file_count in (None, 0)
        or component_count in (None, 0)
        or acceptance_count in (None, 0)
    )
    if file_count in (None, 0):
        reason_codes.append(ReasonCode.INSUFFICIENT_FILE_SIGNAL)
    if component_count in (None, 0):
        reason_codes.append(ReasonCode.INSUFFICIENT_COMPONENT_SIGNAL)
    if acceptance_count in (None, 0):
        reason_codes.append(ReasonCode.INSUFFICIENT_ACCEPTANCE_SIGNAL)

    contradictory = (
        (file_count == 0 and fanout not in (None, 0))
        or (signals.declared_scope is Scope.SIMPLE and file_count not in (None, 1))
        or (signals.declared_scope is Scope.LOCALIZED and file_count is not None and file_count > config.max_localized_files)
        or (signals.declared_scope is Scope.REPOSITORY_WIDE and file_count == 1 and component_count == 1 and fanout == 0)
    )
    if contradictory:
        reason_codes.append(ReasonCode.CONTRADICTORY_SIGNALS)

    ambiguity = _level_for_count(ambiguity_count)
    risk = _level_for_count(risk_count)
    acceptance = _level_for_count(acceptance_count)
    derived = {
        "component_count": component_count,
        "acceptance_check_count": acceptance_count,
        "ambiguity_marker_count": ambiguity_count,
        "risk_marker_count": risk_count,
        "has_shared_state": signals.state_shared,
        "has_architectural_change": signals.architectural_change,
    }

    if incomplete or contradictory or ambiguity_count:
        scope = Scope.UNKNOWN
        path = RecommendedPath.QUALIFICATION_REQUIRED
        confidence = Confidence.LOW
    elif (
        file_count <= config.max_simple_files
        and component_count == 1
        and fanout == 0
        and acceptance_count <= config.max_simple_acceptance_checks
        and not risk_count
    ):
        scope = Scope.SIMPLE
        path = RecommendedPath.SIMPLE_PATH
        confidence = Confidence.HIGH
    elif (
        signals.architectural_change
        or signals.state_shared
        or component_count > config.max_localized_components
        or file_count > config.max_localized_files
        or fanout > config.max_localized_fanout
    ):
        scope = Scope.REPOSITORY_WIDE
        path = RecommendedPath.REPOSITORY_WIDE_PATH
        confidence = Confidence.MEDIUM
    elif file_count >= 1 and component_count >= 1:
        scope = Scope.LOCALIZED
        path = RecommendedPath.LOCALIZED_PATH
        confidence = Confidence.HIGH
    else:
        scope = Scope.UNKNOWN
        path = RecommendedPath.QUALIFICATION_REQUIRED
        confidence = Confidence.LOW

    # A risk marker is observable, but P1 does not turn it into escalation.
    # It only prevents the narrow SIMPLE classification.
    if scope is Scope.SIMPLE and risk_count:
        scope = Scope.UNKNOWN
        path = RecommendedPath.QUALIFICATION_REQUIRED
        confidence = Confidence.LOW

    telemetry = {
        "characterization_duration_ms": characterization_duration_ms,
        "characterization_scope": scope.value,
        "characterization_confidence": confidence.value,
        "recommended_path": path.value,
        "signal_count": sum(
            value is not None
            for value in (
                signals.candidate_files,
                signals.dependency_edges,
                signals.affected_components,
                signals.known_tests,
                signals.ambiguity_markers,
                signals.risk_markers,
                signals.acceptance_checks,
            )
        ),
    }
    return TaskCharacterization(
        schema_version=SCHEMA_VERSION,
        scope=scope,
        estimated_files=file_count,
        dependency_fanout=fanout,
        test_surface=_test_surface(signals.known_tests),
        ambiguity=ambiguity,
        risk=risk,
        acceptance_complexity=acceptance,
        confidence=confidence,
        signals=tuple(dict.fromkeys(reason_codes)),
        recommended_path=path,
        input_signals=signals.to_dict(),
        derived_signals=derived,
        telemetry=telemetry,
    )


def characterize_timed(task_signals: TaskSignals, *, config: CharacterizationConfig = DEFAULT_CONFIG) -> TaskCharacterization:
    """Measure local characterization overhead; no model or executor is called."""

    started = perf_counter_ns()
    result = characterize(task_signals, config=config)
    duration_ms = max(0, (perf_counter_ns() - started) // 1_000_000)
    return replace(result, telemetry={**result.telemetry, "characterization_duration_ms": duration_ms})
