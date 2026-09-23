# Decision 0020 — Contract executor bridge for orchestration

## Status

Accepted as the fifth architecture strengthening block.

## Decision

Add a thin `ContractExecutorRunner` bridge so the existing orchestration gate
can consume the neutral `Executor` protocol while retaining its legacy result
shape during migration. The bridge maps execution state and error only; it
does not run verification, acceptance, promotion or fallback.

## Falsifiable hypothesis

If orchestration can use a neutral executor through one explicit bridge, then
the existing governance, routing, progress, verification and acceptance gates
remain behaviorally stable while the concrete runner becomes replaceable.

## Acceptance criteria

- fake neutral executor reaches existing acceptance flow;
- blocked neutral execution remains blocked;
- task, treatment, sandbox and configuration identity are forwarded;
- no concrete provider or executor is imported by orchestration;
- existing orchestration tests remain passing.
