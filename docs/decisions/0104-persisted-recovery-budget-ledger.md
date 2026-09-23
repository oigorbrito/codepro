# ADR 0104: Persist the updated budget ledger with a new attempt

## Status

Accepted for local architectural evidence.

## Decision

When retry or recovery reservation receives a persisted budget ledger, it
writes `budget-ledger.json` containing the new attempt id before returning the
new artifact root. `ArtifactStore.write_manifest()` requires the manifest's
budget ledger to match that persisted ledger exactly.

## Falsifiable hypothesis and acceptance criteria

H1: accepted attempt reservation cannot leave budget consumption implicit. The
test must observe the new attempt in `budget-ledger.json`; a manifest with a
different ledger must be rejected.

## Consequences

The ledger is copied, not mutated in memory. Callers still need to write the
matching manifest and event log; reservation alone is not execution success.
