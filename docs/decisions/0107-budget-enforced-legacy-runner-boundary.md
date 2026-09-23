# ADR 0107: Budgeted orchestration requires an explicit runner capability

## Status

Accepted for local architectural evidence.

## Decision

When an execution plan carries a budget, the orchestration seam requires the
runner to expose `run_with_budget(request, selection, attempt_id,
budget_ledger)`. A legacy runner that exposes only `run()` is blocked before
execution with `BUDGET_ENFORCEMENT_REQUIRED`. The neutral
`ContractExecutorRunner` implements the capability only after the attempt has
been reserved in the immutable ledger.

## Falsifiable hypothesis and acceptance criteria

H1: a budgeted request cannot reach a runner that has not declared the budget
enforcement capability.

- legacy runner without the capability is blocked before its `run()` method:
  PASS;
- contract bridge requires the reserved attempt identity: PASS;
- missing post-execution usage remains blocked as unavailable: PASS;
- deterministic local suite: 366 tests PASS;
- external qualification: not performed.

## Consequences

The old runner seam is no longer silently trusted for budgeted execution.
Existing adapters must implement the capability or remain explicitly blocked;
this is a compatibility break by design because silent budget bypass is not an
acceptable executor-agnostic behavior.
