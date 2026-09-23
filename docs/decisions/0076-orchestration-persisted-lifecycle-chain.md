# ADR 0076 — Orchestration persists the execution-to-acceptance lifecycle

## Decision

When supplied an attempt-bound `EventLog`, orchestration persists lifecycle
references in causal order:

`plan → preflight? → execution → verification → acceptance`.

Execution, verification, and acceptance references are derived from their
neutral contracts. If a required lifecycle write fails, orchestration returns
an explicit blocked result rather than reporting a later acceptance without
persisted evidence. Promotion remains a separate stage and is not performed by
orchestration.

Legacy callers without an event log remain compatible for non-capability plans,
but they do not produce a replay-complete lifecycle claim.

## Falsifiable hypothesis

An event-backed accepted pipeline replays all persisted stages in order, while
missing persistence prevents an acceptance claim. Tests falsify this if stages
are reordered, references drift, or acceptance is returned after a failed
write.

## Acceptance evidence

The complete local suite ran 327 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests verify persisted plan, execution, verification, and
acceptance references and causal replay.

## Status

Accepted for persisted orchestration lifecycle. Promotion remains an
independent gate.
