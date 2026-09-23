# ADR 0080 — Terminal lifecycle errors are explicit and replayable

## Decision

`EventLog.append_terminal()` persists a single terminal `TASK_FINISHED` fact
with status and optional error code. Repeating the same terminal status is
idempotent; changing a terminal status is rejected. Replay reconstructs the
declared status and error code without creating verification or acceptance
outcomes.

## Falsifiable hypothesis

Blocked, failed, and indeterminate terminal paths can be replayed with their
error code, while terminal status mutation is rejected. Tests falsify this if a
terminal status changes silently or if replay infers later lifecycle stages.

## Acceptance evidence

The complete local suite ran 333 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests cover idempotent terminal persistence, status mutation
rejection, and replay reconstruction.

## Status

Accepted for terminal lifecycle telemetry. Terminal events do not imply
verification, acceptance, or promotion.
