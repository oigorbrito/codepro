"""Minimal, executor-agnostic Arkx execution contracts and telemetry."""

from .contracts import Event, EventType, ExecutionRecord, ExecutionStatus
from .characterization import (
    CharacterizationConfig,
    Confidence,
    RecommendedPath,
    Scope,
    TaskCharacterization,
    TaskSignals,
    characterize,
    characterize_timed,
)
from .progress import (
    ProgressAssessment,
    ProgressConfig,
    ProgressEvidence,
    ProgressSnapshot,
    ProgressStatus,
    assess_progress,
    assess_progress_timed,
)

__all__ = [
    "Event",
    "EventType",
    "ExecutionRecord",
    "ExecutionStatus",
    "CharacterizationConfig",
    "Confidence",
    "RecommendedPath",
    "Scope",
    "TaskCharacterization",
    "TaskSignals",
    "characterize",
    "characterize_timed",
    "ProgressAssessment",
    "ProgressConfig",
    "ProgressEvidence",
    "ProgressSnapshot",
    "ProgressStatus",
    "assess_progress",
    "assess_progress_timed",
]
