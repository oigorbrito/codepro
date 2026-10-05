"""Helpers for staged module-level compatibility with the ``arkx`` namespace."""

from __future__ import annotations

from types import ModuleType


def public_names(module: ModuleType) -> tuple[str, ...]:
    return tuple(sorted(name for name in dir(module) if not name.startswith("_")))


def resolve(module: ModuleType, name: str):
    return getattr(module, name)
