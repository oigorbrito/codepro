# ADR 0101: Recovery manifests must match recovery lineage

## Status

Accepted for local architectural evidence.

## Decision

When an artifact root contains `recovery-lineage.json`,
`ArtifactStore.write_manifest()` validates the lineage before writing the
manifest. Trial, attempt id, attempt number and configuration digest must all
match. A mismatch is rejected before the manifest is persisted.

## Falsifiable hypothesis and acceptance criteria

H1: a recovery directory cannot be made audit-ready by writing an unrelated
manifest. The test must reject a mismatched attempt manifest.

## Consequences

Recovery reservation, manifest persistence and execution remain distinct
states, but the manifest cannot sever the causal identity established at
reservation.
