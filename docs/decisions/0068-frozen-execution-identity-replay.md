# ADR 0068 — Strict replay freezes configuration, budget, and treatment identity

## Decision

Strict restored-chain audit observes `configuration_digest`, `budget_digest`,
and `treatment` from persisted lifecycle events. Values must be homogeneous and,
when expected identity is supplied, equal to the expected values. Audited
experiment validation additionally compares them with the attempt manifest.

This prevents a retry or restoration from reusing an attempt identity with a
different configuration, budget, or treatment. Capability identity is not yet
required because Arkx does not have a canonical persisted capability digest in
the manifest; introducing one without that contract would create false
confidence.

## Falsifiable hypothesis

Configuration drift in a replayed event log is rejected, while an unchanged
identity passes. Tests falsify this if drift is silently accepted or if an
unversioned capability field is treated as qualified evidence.

## Acceptance evidence

The complete local suite ran 316 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests cover configuration drift rejection and manifest/event
identity comparison.

## Status

Accepted for frozen execution identity. Capability registry persistence remains
an explicit future contract, not an inferred field.
