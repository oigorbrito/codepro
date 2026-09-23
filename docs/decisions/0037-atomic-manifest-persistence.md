# ADR 0037 — Atomic persistence of the execution manifest

## Decision

`ArtifactStore.write_manifest` validates attempt identity and lifecycle, then
atomically writes the current `RunManifest` snapshot. This is the persistence
boundary for the budget-aware execution result and its ledger.

The operation does not verify artifacts, accept a patch, promote a treatment,
or infer success from a successful write.

## Acceptance

A valid bound manifest must round-trip from disk. Invalid identity or lifecycle
must be rejected before persistence, and the write must use the existing atomic
artifact-store primitive.
