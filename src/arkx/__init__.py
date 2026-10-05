"""Stable CodePro package boundary with lazy legacy compatibility.

The neutral result contracts are loaded eagerly. Older root-level exports are
resolved only when explicitly requested, preserving existing imports without
reintroducing the eager experimental import graph.
"""

from __future__ import annotations

from importlib import import_module

__version__ = "0.3.0.dev0"

from .execution import ExecutionResult
from .orchestration_result import ExecutionResult as OrchestrationExecutionResult

_LEGACY_MODULES = (
    "contracts", "configuration", "event_log", "integration", "execution",
    "harness", "outcomes", "verifier", "request", "selection",
    "p82_localization", "p82_editing", "orchestration", "recovery",
    "acceptance", "promotion", "characterization", "progress", "routing",
    "planning", "verification", "handoff", "composition",
    "executor_qualification", "p82", "p82_baseline", "performance_baseline",
    "swebench_authority",
)


def __getattr__(name: str):
    """Resolve a legacy root export without eager subsystem imports."""
    if name == "OrchestrationExecutionResult":
        return OrchestrationExecutionResult
    for module_name in _LEGACY_MODULES:
        qualified_name = f"{__name__}.{module_name}"
        try:
            module = import_module(qualified_name)
        except ModuleNotFoundError as error:
            if error.name != qualified_name:
                raise
            continue
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | {"OrchestrationExecutionResult"})


__all__ = ["ExecutionResult", "OrchestrationExecutionResult"]
