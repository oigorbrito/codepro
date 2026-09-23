# ADR 0038 — Persistent lifecycle event log

## Decision

Arkx adds `EventLog` over the existing neutral `Event` contract. Events are
persisted as deterministic JSONL, read back in order, and validated for matching
`run_id` and monotonic timestamps. Writes replace the complete serialized log
atomically; callers use the log serially as an append-only record.

The log records telemetry only. It does not infer acceptance, choose an
executor, or replace the manifest, verification, or promotion states.

## Acceptance

Events must round-trip, wrong run identities must be rejected, timestamp
regression must be rejected, and no external executor/provider is invoked.
