# ADR 0044 — Replay classification against the validated attempt inventory

## Decision

`classify_snapshot_chain_references` classifies replay chain references only
against paths and manifest references already validated by an
`AttemptSnapshot`. It does not scan arbitrary directories, dereference external
URIs, or select a replacement artifact.

## Acceptance

References present in the snapshot inventory are `PRESENT`; absent references
are `MISSING`; and the previous indeterminate behavior remains available when no
inventory is supplied.
