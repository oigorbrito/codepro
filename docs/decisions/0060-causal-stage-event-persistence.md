# ADR 0060 — Persist causal lifecycle stages as replayable events

## Decision

`EventLog.append_stage()` persists request, plan, execution, recovery,
verification, acceptance, and promotion references as causal stage events.
Identical repeated references are idempotent. A different reference for an
already recorded stage is rejected, and `replay_chain()` rejects stage
reference drift or out-of-order events.

The event log stores facts only; it does not execute an adapter, evaluate a
patch, accept a task, or promote a candidate.

## Falsifiable hypothesis

Equivalent event histories replay to the same chain, duplicate stage writes do
not create new facts, and reference mutation cannot be silently accepted.
Tests falsify this if replay fills missing stages, accepts stage drift, or
reexecutes any external component.

## Acceptance evidence

The complete local suite ran 306 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests cover causal append, idempotent duplicate handling,
out-of-order rejection, and reference drift detection.

## Status

Accepted for persistent lifecycle telemetry and replay. No external execution
or promotion is performed by the log.
