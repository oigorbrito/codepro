# ADR 0082: Neutral lifecycle persistence error taxonomy

## Status

Accepted for local architectural evidence; not an external qualification.

## Context

The orchestration lifecycle persists plan, preflight, execution, verification,
acceptance, and terminal events. A missing event log is a capability-specific
precondition when a plan requires persisted capability evidence. Other
persistence failures are generic lifecycle failures and must not be reported
as capability failures.

## Decision

Use `CAPABILITY_PREFLIGHT_PERSISTENCE_REQUIRED` only when a capability-bearing
plan cannot persist its required preflight evidence. Use
`LIFECYCLE_PERSISTENCE_FAILED` for generic stage persistence failures and for a
failure to append the terminal lifecycle event. No fallback executor or
implicit success is permitted.

## Falsifiable hypothesis and acceptance criteria

H1: persistence failures are classified by the violated lifecycle invariant,
not by the last feature added. The focused regression test must distinguish the
generic and capability-specific reasons, and terminal persistence failure must
remain explicit.

## Evidence

Raw evidence is recorded in
`logs/architecture/lifecycle-persistence-error-taxonomy-block-20260923.json`.
The local deterministic suite passed with 334 tests. This is local evidence
only; no provider, model, Docker, or SWE-bench qualification was performed.

## Consequences

Operators can distinguish a missing capability-evidence precondition from a
general lifecycle persistence outage. Callers still need to decide whether a
blocked result is retryable according to policy; the taxonomy does not grant
automatic retry or promotion.
