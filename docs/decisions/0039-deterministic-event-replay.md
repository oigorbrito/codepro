# ADR 0039 — Deterministic event replay

## Decision

Arkx adds `replay_events`, a pure reducer over persisted `Event` values. It
reconstructs declared facts such as event count, executor invocations, retries,
evidence references, and the status explicitly declared by `TASK_FINISHED`.

Replay does not invoke an executor, rerun verification, infer acceptance, or
replace the manifest. Missing facts remain missing.

## Acceptance

Equivalent event sequences produce the same `ReplayState`; wrong run identity
and timestamp regression are rejected; replay performs no external calls.
