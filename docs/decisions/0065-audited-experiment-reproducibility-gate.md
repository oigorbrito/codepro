# ADR 0065 — Reproducible experiments require audited attempt chains

## Decision

`validate_experiment_record_audited()` extends experiment validation for
decision-grade use. It requires one audit per recorded attempt, matching replay
run identity, `COMPLETE` chain integrity, and presence of every declared
verification, acceptance, and promotion reference in the audited chains.

The existing `validate_experiment_record()` remains available for compatibility
with historical records and basic reference validation. It must not be
interpreted as proof of reproducibility without the audited variant.

## Falsifiable hypothesis

An experiment with an incomplete attempt chain or a declared reference absent
from the replayed chain is rejected as reproducible, while a complete matching
experiment passes without rerunning any external component. Tests falsify this
if incomplete evidence is accepted.

## Acceptance evidence

The complete local suite ran 314 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests cover complete audited experiment acceptance and
incomplete-chain rejection.

## Status

Accepted for reproducibility claims. No benchmark, provider, or model is
qualified by this local validator.
