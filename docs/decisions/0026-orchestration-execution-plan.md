# Decision 0026 — Orchestration produces an execution plan

## Status

Accepted as the eleventh architecture strengthening block.

## Decision

After governance, characterization, routing and selection gates pass,
orchestration produces an immutable `ExecutionPlan` before invoking the
executor. The plan is included in the orchestration result and does not
contain execution, verification, acceptance or promotion outcomes.

## Falsifiable hypothesis

If equivalent authorized inputs produce the same plan before execution, then
execution intent can be audited and compared independently of executor output.

## Acceptance criteria

- plan is produced only after required gates pass;
- equivalent inputs produce deterministic plan identity;
- terminal orchestration results retain the plan;
- executor output cannot mutate the plan;
- existing orchestration behavior remains passing.
