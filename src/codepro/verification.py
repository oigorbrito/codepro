"""Canonical facade for patch-verification contracts."""

from arkx import verification as _legacy
from ._legacy_module import public_names, resolve

__all__ = public_names(_legacy)


def __getattr__(name: str):
    return resolve(_legacy, name)
