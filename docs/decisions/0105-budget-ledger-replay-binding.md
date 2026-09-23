# ADR 0105: Budget ledger is part of execution replay

## Status

Accepted for local architectural evidence.

## Decision

Replay captures the `budget_ledger` carried by execution evidence. Repeated
ledger facts must be identical; drift is rejected. When an audited manifest
declares a persisted budget ledger, `audit_restored_chain()` requires the
replayed ledger to match it exactly.

## Falsifiable hypothesis and acceptance criteria

H1: budget consumption cannot differ between artifact manifest and event-log
replay. Tests must restore a ledger and reject a changed ledger fact.

## Consequences

Budget state is now part of the reproducibility chain. Legacy attempts without
ledger evidence remain weaker and are not upgraded by inference.
