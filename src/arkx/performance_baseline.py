"""Measurement-only baseline for local and controlled-path overhead.

This module records observed cost. It does not optimize, classify quality, or
promote a path. A failed operation is retained as evidence instead of being
treated as a zero-duration success.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from time import perf_counter_ns
from typing import Any, Callable

from .characterization import TaskSignals, characterize_timed
from .contracts import Event, EventType
from .submission import SubmissionArtifact


SCHEMA_VERSION = 1
DEFAULT_SAMPLES = 5


@dataclass(frozen=True)
class Measurement:
    name: str
    samples: tuple[int, ...]
    status: str
    error: str | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        ordered = sorted(self.samples)
        return {
            "name": self.name,
            "sample_count": len(self.samples),
            "durations_ns": list(self.samples),
            "min_ns": min(self.samples) if self.samples else None,
            "median_ns": ordered[len(ordered) // 2] if ordered else None,
            "max_ns": max(self.samples) if self.samples else None,
            "status": self.status,
            "error": self.error,
            "metadata": self.metadata or {},
        }


def _measure(name: str, operation: Callable[[], Any], *, samples: int) -> Measurement:
    durations: list[int] = []
    error: str | None = None
    for _ in range(samples):
        started = perf_counter_ns()
        try:
            operation()
        except Exception as exc:  # retain the failure as evidence
            error = f"{type(exc).__name__}: {exc}"
            return Measurement(name, tuple(durations), "BLOCKED", error)
        durations.append(perf_counter_ns() - started)
    return Measurement(name, tuple(durations), "PASS", metadata={})


def _git_identity(workspace: Path) -> dict[str, Any]:
    observations: dict[str, Any] = {}
    for name, command in (
        ("head", ["git", "rev-parse", "HEAD"]),
        ("branch", ["git", "branch", "--show-current"]),
        ("status", ["git", "status", "--short", "--untracked-files=all"]),
    ):
        result = subprocess.run(command, cwd=workspace, text=True, capture_output=True, check=False)
        observations[name] = {
            "command": " ".join(command),
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    return observations


def _event_log_operation(event_count: int) -> Callable[[], None]:
    def operation() -> None:
        with tempfile.TemporaryDirectory(prefix="codepro-baseline-") as directory:
            path = Path(directory) / "events.jsonl"
            with path.open("w", encoding="utf-8", newline="\n") as stream:
                for index in range(event_count):
                    event = Event(
                        f"2026-01-01T00:00:{index:02d}+00:00",
                        EventType.EVIDENCE_ADDED,
                        "baseline-run",
                        {"index": index},
                    )
                    stream.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")

    return operation


def collect_baseline(workspace: str | Path, *, samples: int = DEFAULT_SAMPLES) -> dict[str, Any]:
    """Collect a raw, repeatable cost baseline for the current workspace."""

    if samples < 1:
        raise ValueError("samples must be positive")
    root = Path(workspace).resolve()
    signals = TaskSignals(
        candidate_files=("notes.txt",),
        dependency_edges=(),
        affected_components=("local-text",),
        known_tests=("tests/test_performance_baseline.py",),
        ambiguity_markers=(),
        risk_markers=(),
        acceptance_checks=("baseline recorded",),
        state_shared=False,
        architectural_change=False,
    )
    measurements = [
        _measure(
            "workspace_submission_capture",
            lambda: SubmissionArtifact.from_git_workspace(root),
            samples=samples,
        ),
        _measure("characterization", lambda: characterize_timed(signals), samples=samples),
    ]
    for event_count in (1, 10, 50):
        measurements.append(
            _measure(
                f"telemetry_event_append_{event_count}",
                _event_log_operation(event_count),
                samples=samples,
            )
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "baseline_type": "LOCAL_OVERHEAD_BASELINE",
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "workspace": str(root),
        "python": sys.version,
        "platform": platform.platform(),
        "git_identity": _git_identity(root),
        "sample_policy": {"warmups": 0, "samples": samples},
        "measurements": [measurement.to_dict() for measurement in measurements],
        "interpretation": {
            "quality_claim": "NOT_MADE",
            "agility_impact": "NOT_VERIFIED",
            "optimization": "NOT_EXECUTED",
        },
    }


def write_baseline(report: dict[str, Any], output: str | Path) -> Path:
    """Persist raw baseline evidence atomically and return its path."""

    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(destination)
    return destination


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Collect CodePro local overhead baseline evidence.")
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--output", required=True)
    parser.add_argument("--samples", type=int, default=DEFAULT_SAMPLES)
    args = parser.parse_args(argv)
    report = collect_baseline(args.workspace, samples=args.samples)
    write_baseline(report, args.output)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
