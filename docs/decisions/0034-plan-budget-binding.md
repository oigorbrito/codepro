# ADR 0034 — Binding between execution plan and budget specification

## Decision

`ExecutionPlan` may carry an `ExecutionBudgetSpec`. When present, its
`budget_digest` is derived or validated against that specification. The routed
orchestration path materializes the request budget into this neutral spec before
execution.

Legacy plans containing only a digest remain valid. The plan still does not
consume budget or invoke an executor as a side effect.

## Acceptance

The plan must serialize the budget, derive a missing digest, reject a mismatched
digest, and preserve the binding through routed orchestration.
