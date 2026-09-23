# ADR 0078 — Replay reconstructs operational telemetry without inferring success

## Decision

Persisted lifecycle events may carry operational facts for execution outcome,
preflight status, promotion status, and structured error codes. `ReplayState`
reconstructs these fields deterministically in addition to stage references,
verification state, and acceptance decision.

These fields are diagnostic facts only. Replay does not infer acceptance,
promotion, retryability, or provider quality from their presence.

## Falsifiable hypothesis

Equivalent event histories reconstruct equivalent operational telemetry, and a
legacy error representation remains readable without crashing replay. Tests
falsify this if telemetry changes the lifecycle decision implicitly or if
structured error data is lost.

## Acceptance evidence

The complete local suite ran 330 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests cover reconstruction of execution outcome and error
codes and compatibility with legacy textual errors.

## Status

Accepted for replay observability. No lifecycle outcome is promoted by
telemetry alone.
