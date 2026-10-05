"""Canonical CodePro namespace during the staged ``arkx`` migration.

The implementation remains in ``arkx`` for this migration slice.  This
facade gives new consumers the product namespace while keeping the legacy
namespace available until the supported API has been migrated and tested.
"""

from __future__ import annotations

import arkx as _legacy

from ._version import __version__

__all__ = tuple(_legacy.__all__)


def __getattr__(name: str):
    """Resolve a supported public symbol from the legacy implementation."""
    return getattr(_legacy, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
