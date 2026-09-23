# ADR 0079 — Replay telemetry must match loaded result objects

## Decision

`validate_replay_telemetry()` compares persisted replay facts with any loaded
execution, verification, acceptance, and promotion objects. It rejects
execution outcome, structured error code, verification state, acceptance
decision, or promotion status drift.

The validator is observational: it does not rerun an executor, verifier,
acceptance authority, or promotion policy. Missing telemetry remains a separate
incompleteness concern and is not filled by inference.

## Falsifiable hypothesis

Matching persisted facts and result objects pass; any recorded mismatch fails.
Tests falsify this if stale telemetry is accepted or if validation invokes an
external component.

## Acceptance evidence

The complete local suite ran 331 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests cover verification-state drift against a loaded result.

## Status

Accepted for replay integrity. No lifecycle state is promoted by telemetry
validation alone.
