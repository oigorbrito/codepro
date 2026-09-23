# Decision 0022 — Legacy execution result boundary

## Status

Accepted as the seventh architecture strengthening block.

## Decision

Centralize conversion from the neutral `arkx.execution.ExecutionResult` to the
legacy orchestration result shape in `legacy_execution_from_contract`. The
legacy shape remains a compatibility boundary and is not a second execution
contract.

## Falsifiable hypothesis

If all neutral-to-legacy conversion is deterministic and centralized, then
orchestration compatibility can be maintained while new executors depend only
on the neutral contract.

## Acceptance criteria

- conversion preserves terminal state, artifact references and error message;
- direct and bridged orchestration remain equivalent;
- no second provider/executor selection logic is introduced;
- legacy result remains confined to the compatibility boundary.
