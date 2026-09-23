# ADR 0045 — Explicit replay-chain integrity states

## Decision

Arkx adds `ChainIntegrity` with `COMPLETE`, `INCOMPLETE`, and `INCONSISTENT`.
The assessment uses only the explicit chain and its reference report: missing
stages or indeterminate inventory are incomplete; missing references in a known
inventory are inconsistent; all stages present and verified are complete.

This classification is a precondition signal only. It does not accept, reject,
promote, repair, or reexecute a task.

## Acceptance

The three states must be distinguishable with deterministic tests and no
external calls.
