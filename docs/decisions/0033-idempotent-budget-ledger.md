# ADR 0033 — Idempotent execution budget ledger

## Decision

Arkx adds an immutable `BudgetLedger` over `ExecutionBudgetSpec`. Consumption
is keyed by `attempt_id`, so repeating the same consumption is an explicit
`ALREADY_CONSUMED` result and does not double-count usage. A rejected
consumption returns the unchanged ledger with a concrete limit reason.

The ledger does not retry, execute, persist itself, or reconcile the separate
request/routing/recovery/qualification budgets yet.

## Acceptance

Equivalent ledger inputs are deterministic; an attempt is consumed at most
once; exceeded limits do not mutate the ledger; and no executor is invoked.
