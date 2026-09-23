# Decision 0023 — Public execution result boundary

## Status

Accepted as the eighth architecture strengthening block.

## Evidence

The package initializer imported both the neutral execution contract and the
legacy orchestration result under the same public name. Import order caused
the legacy type to overwrite `arkx.ExecutionResult`, making the public API
executor-dependent despite the new neutral contract.

## Decision

`arkx.ExecutionResult` is the neutral contract. The legacy orchestration shape
is exposed as `arkx.OrchestrationExecutionResult` during migration. Internal
legacy imports remain valid in their module boundary.

## Acceptance criteria

- public `arkx.ExecutionResult` is the neutral type;
- public legacy result has an explicit distinct name;
- no import-order collision remains;
- existing focused tests pass.
