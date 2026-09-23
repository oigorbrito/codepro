# ADR 0062 — Restored attempts require manifest, event, and outcome consistency

## Decision

`audit_restored_chain()` loads the event log for the restored attempt, replays
its facts, validates replayed terminal status against the manifest, reconstructs
the causal chain, classifies references against the snapshot and supplied
outcomes, and validates outcome-object identity when all outcomes are present.

The audit does not rerun execution or evaluation. An incomplete chain remains
`INCOMPLETE`; missing references are not inferred from nearby artifacts.
Manifest/replay divergence is rejected as an integrity error.

## Falsifiable hypothesis

A restored attempt with matching facts is auditable without execution, while a
manifest/replay status mismatch or outcome-reference drift is rejected. Tests
falsify this if audit executes external components or reports an incomplete
chain as complete.

## Acceptance evidence

The complete local suite ran 310 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests cover restored replay, incomplete-chain reporting, and
manifest status divergence.

## Status

Accepted for artifact restoration and audit. No external execution or
promotion is performed by restoration.
