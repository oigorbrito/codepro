# Decision 0025 — Explicit execution plan boundary

## Status

Accepted as the tenth architecture strengthening block.

## Decision

Introduce `ExecutionPlan` as the frozen intent for one execution path. It
records task, treatment, executor/provider/model identities, sandbox, budget,
configuration and ordered steps. It can produce an `ExecutionRequest`, but it
does not contain execution result, verification, acceptance or promotion.

## Falsifiable hypothesis

If plan and result are separate contracts, routing and orchestration can be
tested for deterministic planning without invoking an executor.

## Acceptance criteria

- plan serialization is deterministic;
- plan identity fields are validated;
- plan-to-request conversion preserves declared identities;
- result state is not present in the plan;
- no executor/provider is invoked by plan construction.
