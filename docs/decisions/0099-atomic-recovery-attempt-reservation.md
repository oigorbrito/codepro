# ADR 0099: Recovery attempt reservation is atomic and lineage-bound

## Status

Accepted for local architectural evidence.

## Decision

`ArtifactStore.reserve_recovery_attempt()` validates the source attempt id,
derives the next attempt id, reserves a new directory, and atomically writes
`recovery-lineage.json`. Existing directories are never overwritten. Manifest
creation and execution remain separate operations.

## Falsifiable hypothesis and acceptance criteria

H1: a recovery attempt cannot overwrite an existing attempt or lose its source
lineage. Tests must inspect the lineage and reject a second reservation.

## Consequences

The artifact boundary is safe for a future resume service. It still does not
authorize execution, promotion, or automatic executor switching.
