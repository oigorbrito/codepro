# ADR 0106: Retry and recovery lineage must match the replayed event chain

## Status

Accepted for local architectural evidence.

## Decision

An audited retry or recovery attempt is valid only when its persisted lineage
agrees with the replayed event chain. The execution reference must identify the
manifest attempt, a recovery lineage must identify the persisted recovery
reference and source attempt, and the replayed budget ledger must equal the
manifest ledger when one is declared.

## Falsifiable hypothesis and acceptance criteria

H1: an attempt with inconsistent execution, recovery, source, or budget facts
cannot pass lineage audit.

- matching execution/recovery/source/ledger facts: PASS;
- missing or mismatched recovery reference: PASS rejection;
- local regression suite: 365 tests PASS;
- external qualification: not performed.

## Consequences

Recovery evidence is now causally bound to the attempt being audited. Legacy
attempts without these facts remain weaker and are not upgraded by inference.
