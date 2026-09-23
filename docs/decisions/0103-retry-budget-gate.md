# ADR 0103: Retry reservation uses the same persisted attempt budget

## Status

Accepted for local architectural evidence.

## Decision

`ArtifactStore.reserve_retry_attempt()` applies the same optional persisted
ledger gate as recovery reservation. The previous attempt must be consumed and
the next attempt must remain within `max_attempts`; otherwise no directory or
lineage is written.

## Falsifiable hypothesis and acceptance criteria

H1: retry and recovery cannot disagree about attempt-budget enforcement. The
test must reject retry reservation at an exhausted budget and prove no target
directory exists.
