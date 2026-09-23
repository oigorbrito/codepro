# ADR 0035 — Persisted budget ledger binding

## Decision

`RunManifest` may persist a serialized budget ledger bound to its own
`attempt_id` and `budget_digest`. `with_budget_ledger` returns a new manifest
snapshot and rejects a ledger from another attempt or configuration.

This is a persistence boundary only. It does not make the executor consume the
ledger automatically and does not merge the ledger with other budget scopes.

## Acceptance

The bound manifest must round-trip its ledger, reject attempt mismatch and
digest mismatch, and remain immutable from the caller's perspective.
