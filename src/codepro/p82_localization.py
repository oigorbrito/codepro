"""Canonical facade for P8.2 localization contracts."""

from arkx import p82_localization as _legacy
from ._legacy_module import public_names, resolve

__all__ = public_names(_legacy)


def __getattr__(name: str):
    return resolve(_legacy, name)
