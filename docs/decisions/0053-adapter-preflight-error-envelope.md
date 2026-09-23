# ADR 0053 — Adapter preflight errors retain neutral boundaries

## Decision

When an adapter preflight is not ready, Arkx converts it to the common
`ErrorEnvelope` through `preflight_error`. The mapping retains the integration
boundary (`EXECUTOR`, `PROVIDER`, `SANDBOX`, or `VERIFICATION`), uses a stable
`PREFLIGHT_<STATUS>` code, and attaches the deterministic preflight reference
as raw evidence.

Retryability is `UNKNOWN` unless a later, explicit policy has enough evidence
to classify it. Missing identity, missing dependency, permission denial, and
runtime failure therefore cannot silently become retryable, successful, or a
fallback selection.

## Falsifiable hypothesis

For equivalent preflight observations, the resulting error envelope preserves
the same boundary, code, retryability, and raw evidence reference. A test can
falsify this by observing boundary drift, inferred retryability, or missing
preflight evidence.

## Acceptance evidence

The dependency-isolated suite ran 294 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`; the OpenRouter adapter test remains excluded because the
`minisweagent` dependency is unavailable. Concrete adapter states remain
recorded as `BLOCKED` or `UNKNOWN` in the read-only preflight evidence and are
not qualified by this local result.

## Status

Accepted for neutral contract development. No external adapter or provider is
promoted.
