"""Canonical facade for the orchestration compatibility boundary."""

from arkx import orchestration as _legacy
from ._legacy_module import public_names, resolve

__all__ = public_names(_legacy)


def __getattr__(name: str):
    return resolve(_legacy, name)
