# ADR 0036 — Budget-aware execution lifecycle

## Decision

`ContractRun.execute_with_budget` consumes the immutable budget ledger before
invoking an executor. Accepted consumption proceeds to execution and carries
the updated ledger. Rejected consumption returns a structured `BLOCKED` result
and invokes no executor.

This boundary does not persist the manifest itself, retry automatically, or
merge unrelated budget scopes.

## Acceptance

Fake execution must prove both orderings: accepted budget leads to one executor
invocation and updated ledger; exhausted budget leads to structured blocked
state and zero executor invocations.
