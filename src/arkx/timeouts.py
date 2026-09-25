"""Timeout provenance; a duration is not an authority by itself."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TimeoutOrigin(str, Enum):
    PROVIDER = "provider_timeout"
    MODEL_RETRY = "model_retry_timeout"
    ENVIRONMENT_COMMAND = "environment_command_timeout"
    AGENT_WALL = "agent_wall_timeout"
    RUNNER_WATCHDOG = "runner_watchdog"
    EVALUATOR = "evaluator_timeout"
    CONTAINER_START = "container_start_timeout"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class TimeoutObservation:
    origin: TimeoutOrigin
    configured_value: float | None
    authority_source: str | None
    observed_trigger: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "origin": self.origin.value,
            "configured_value": self.configured_value,
            "authority_source": self.authority_source,
            "observed_trigger": self.observed_trigger,
        }
