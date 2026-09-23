# ADR 0031 — Artifact-store reservation for retry lineage

## Decision

`ArtifactStore` exposes an explicit `reserve_retry_attempt` operation. It
validates the previous attempt identity, creates the next append-only attempt
directory, and atomically records `retry-lineage.json` with both identities and
the configuration digest.

The operation refuses identity drift and existing attempt directories. It does
not execute, verify, accept, promote, or recover a task.

## Acceptance

The store must preserve the previous attempt, persist the new lineage, reject
duplicate reservation, reject identity drift, and never silently overwrite an
attempt directory.
