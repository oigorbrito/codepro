"""Canonical facade for the deterministic baseline fixture."""

from arkx import baseline as _legacy
from ._legacy_module import public_names, resolve

__all__ = public_names(_legacy)


def __getattr__(name: str):
    return resolve(_legacy, name)
