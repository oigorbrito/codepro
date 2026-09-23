# ADR 0089: Bind canonical configuration snapshots to execution plans

## Status

Accepted for local architectural evidence.

## Decision

`ExecutionPlan.configuration_snapshot` is optional for compatibility, but when
present its canonical digest is the plan's `configuration_digest`. A plan may
derive the digest from the snapshot or reject a mismatching supplied digest.
The serialized plan retains the snapshot metadata and public values, never
secret material.

## Falsifiable hypothesis and acceptance criteria

H1: a plan cannot carry a configuration digest inconsistent with its canonical
snapshot. Tests must derive a missing digest and reject an inconsistent one.

## Consequences

Adapters can progressively migrate from opaque strings to canonical snapshots.
Plans without snapshots remain valid legacy contracts but are weaker for
reproducibility and should be treated as such by qualification policy.
