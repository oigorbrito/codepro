# ADR 0075 — Orchestration persists preflight before execution

## Decision

The causal replay chain includes an optional `preflight` stage between plan and
execution. When a plan requires capabilities, orchestration must receive an
attempt-bound `EventLog` and persist the preflight reference before invoking
the executor.

If the preflight is absent, mismatched, denied by policy, or cannot be
persisted because no attempt-bound event log exists, orchestration blocks. It
does not fabricate a run identity or select a fallback.

## Falsifiable hypothesis

A capability-requiring orchestration path cannot invoke an executor before a
preflight event is persisted, and replay reconstructs that stage in causal
order. Tests falsify this if execution occurs without the event or if preflight
is replayed after execution.

## Acceptance evidence

The complete local suite ran 326 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests cover missing event-log persistence and preflight stage
handling.

## Status

Accepted for preflight persistence. No external executor or provider is
qualified by event persistence alone.
