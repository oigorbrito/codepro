# Decision 0014 — Reproducible harness identity and failure contract

## Status

Accepted as a compatibility-preserving contract slice.

## Evidence

Current P8.2 artifacts contain multiple report shapes and failure vocabularies.
Some attempts preserve `model_usage` or observed retries as `null`, and the
same task-level run identity appears in different rerun artifact roots. The
documents require immutable attempts and complete identity, but no common
executor-neutral manifest enforced those requirements.

## Decision

Introduce a small executor-neutral contract with four identity levels:

```text
experiment_id -> trial_id -> attempt_id -> artifact references
```

`RunManifest` records the frozen identity and terminal state of one attempt.
`ErrorEnvelope` records error domain, stable code, retryability and raw
evidence references. The contract does not execute, retry, verify, accept or
promote anything.

`attempt_id` is deterministic for `(trial_id, attempt_number,
configuration_digest)` and does not use timestamps or fallback selection.

The P8.2 runner now emits the common error envelope in both `manifest.json`
and the compatibility `execution.json`. The legacy failure category remains
available during migration, but provider, sandbox, harness and executor
domains are mapped explicitly instead of being inferred by consumers.

## Falsifiable hypothesis

If harness artifacts use separate trial/attempt identities and a common error
envelope, then equivalent frozen inputs will serialize identically, distinct
attempts will not collide, and infrastructure/provider failures can be
classified without being represented as task acceptance outcomes.

## Acceptance criteria

1. deterministic contract tests pass;
2. missing identity and invalid attempt numbers are rejected;
3. raw evidence references and retryability survive serialization;
4. existing P0–P8 contracts remain compatible;
5. the P8.2 baseline runner may emit the common manifest while retaining the
   legacy `execution.json` for compatibility; no executor is promoted by this
   slice.

## Non-goals

This decision does not introduce a persistence backend, event bus, replay
engine, executor implementation, provider selection, or sandbox abstraction.
