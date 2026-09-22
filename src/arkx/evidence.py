"""Fail-closed separation between execution result, evidence, and final status."""

from __future__ import annotations

from collections.abc import Iterable

from .contracts import ExecutionStatus


def resolve_status(
    requested: ExecutionStatus | str | None,
    evidence_refs: Iterable[str],
) -> ExecutionStatus:
    """Resolve a status without allowing missing evidence to become PASS.

    This function does not verify evidence quality. It only enforces the P0
    boundary: a requested PASS requires at least one explicit evidence ref.
    """

    status = ExecutionStatus(requested) if requested is not None else ExecutionStatus.NOT_EXECUTED
    refs = list(evidence_refs)
    if status is ExecutionStatus.PASS and not refs:
        return ExecutionStatus.UNVERIFIED
    return status

