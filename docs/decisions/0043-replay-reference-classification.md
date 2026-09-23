# ADR 0043 — Replay reference classification

## Decision

Arkx adds `classify_chain_references` and `ReferenceReport` to classify explicit
chain references against an available artifact inventory. References are
`PRESENT` when found, `MISSING` when an inventory exists and does not contain
them, and `INDETERMINATE` when no inventory is supplied.

The classifier does not dereference arbitrary URIs, download artifacts, or
infer that a recorded reference is physically valid.

## Acceptance

Known present and missing references are distinguished; absent inventory yields
indeterminate; no status is converted to success by inference.
