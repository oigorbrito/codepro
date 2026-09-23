# ADR 0055 — Normalize adapter failures at the integration boundary

## Decision

Arkx exposes neutral error normalization for three concrete failure shapes:

- provider payloads containing an `error` object;
- process failures from executor, sandbox, or evaluator boundaries;
- adapter exceptions.

The result is always an `ErrorEnvelope` with an explicit domain, stable code,
raw evidence references, and `Retryability.UNKNOWN` unless a separate policy
has justified a stronger classification. Provider SDKs and concrete runtime
types are not imported by the core normalization functions.

## Falsifiable hypothesis

Equivalent provider payloads and process failures produce deterministic domain
and code values while preserving raw references. A test falsifies this if a
provider payload reaches the success parser, a sandbox error becomes a provider
error, or retryability is inferred without policy evidence.

## Acceptance evidence

The complete local suite ran 301 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. The OpenRouter adapter test verifies that its provider error
can cross into `ErrorEnvelope`; concrete provider/runtime qualification remains
outside this local result.

## Status

Accepted for neutral integration-boundary development. No adapter is promoted.
