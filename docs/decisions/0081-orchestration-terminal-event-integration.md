# ADR 0081 — Orchestration records terminal status after persisted lifecycle

## Decision

When an attempt-bound event log is supplied, orchestration appends one terminal
`TASK_FINISHED` event after execution/verification/acceptance outcomes, carrying
the orchestration status and primary reason code. Terminal append is idempotent
and does not create missing verification or acceptance stages.

Pre-execution governance failures without a legitimate `run_id` do not receive
a fabricated terminal event. Persistence failure downgrades the returned
result to an explicit blocked state.

## Falsifiable hypothesis

An event-backed pipeline replays its terminal status, while a pre-execution
failure without attempt identity does not fabricate lifecycle facts. Tests
falsify this if terminal status is absent after a run or if an unmaterialized
request receives an attempt event.

## Acceptance evidence

The complete local suite ran 333 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. The persisted orchestration lifecycle test verifies terminal
status replay.

## Status

Accepted for terminal orchestration telemetry. Terminal status remains separate
from promotion.
