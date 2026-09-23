# ADR 0054 — Concrete adapter modules are import-safe but execution-strict

## Decision

Concrete adapter modules may be imported when their external dependency is
absent, so contract and diagnostic tests can run. They must not provide a
substitute implementation: construction or execution raises an explicit
boundary error until the required dependency is available.

This separates module discovery and preflight from runtime qualification. It
does not make an adapter `READY`, and it does not authorize fallback selection.

## Falsifiable hypothesis

The complete test discovery can import adapter modules without the external
runtime, while constructing an unavailable adapter still fails explicitly. A
test falsifies this if import fails globally or if construction silently uses a
fallback.

## Acceptance evidence

The complete local suite ran 298 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. The read-only concrete preflight still reports OpenRouter and
Git Bash as `BLOCKED`, Docker/SWE-bench as `BLOCKED`, and Ollama as `UNKNOWN`.
These results are integration diagnostics, not provider or benchmark
qualification.

## Status

Accepted for integration-boundary development. No concrete adapter is
promoted.
