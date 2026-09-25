"""Legacy orchestration result compatibility types.

This module deliberately has no dependency on the orchestration pipeline so
the package can preserve the legacy result name without importing routing or
experimental subsystems.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExecutionOutcome(str, Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    NOT_EXECUTED = "NOT_EXECUTED"


@dataclass(frozen=True)
class ExecutionResult:
    run_id: str
    outcome: ExecutionOutcome
    evidence_refs: tuple[str, ...] = ()
    error: str | None = None
    telemetry: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "outcome": self.outcome.value,
            "evidence_refs": sorted(set(self.evidence_refs)),
            "error": self.error,
            "telemetry": self.telemetry,
        }
