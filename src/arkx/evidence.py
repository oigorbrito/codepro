"""Fail-closed separation between execution result, evidence, and final status."""

from __future__ import annotations

from collections.abc import Iterable

from .contracts import ExecutionStatus


def normalize_evidence_refs(evidence_refs: Iterable[str]) -> tuple[str, ...]:
    """Return only explicit, non-blank evidence references."""

    normalized: list[str] = []
    for ref in evidence_refs:
        if not isinstance(ref, str):
            raise ValueError("evidence references must be strings")
        value = ref.strip()
        if value:
            normalized.append(value)
    return tuple(normalized)


def resolve_status(
    requested: ExecutionStatus | str | None,
    evidence_refs: Iterable[str],
) -> ExecutionStatus:
    """Resolve a status without allowing missing evidence to become PASS.

    This function does not verify evidence quality. It only enforces the P0
    boundary: a requested PASS requires at least one explicit evidence ref.
    """

    status = ExecutionStatus(requested) if requested is not None else ExecutionStatus.NOT_EXECUTED
    refs = normalize_evidence_refs(evidence_refs)
    if status is ExecutionStatus.PASS and not refs:
        return ExecutionStatus.UNVERIFIED
    return status

