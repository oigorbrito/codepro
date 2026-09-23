# ADR 0028 — Executor-neutral execution budget specification

## Decision

Arkx adds `ExecutionBudgetSpec` as the neutral declaration of attempt, token,
wall-time, cost, and executor-invocation limits. The declaration validates
non-negative values and produces a stable digest for plan and manifest identity.

It does not consume budget, retry, escalate, or override request governance.
Existing routing, recovery, qualification, and request budgets remain separate
until their semantics are reconciled by a later evidence-backed change.

## Rationale

The repository currently has several budget types with different scopes. A
shared execution-level shape is useful for reproducibility, but silently
merging all budget semantics would create an unsafe architectural assumption.
This block adds only the common declaration and identity boundary.

## Acceptance

Equivalent values must produce the same digest; negative values must be rejected;
no executor or provider is invoked by the contract.
