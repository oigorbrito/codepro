# ADR 0108: Orchestration persists the typed configuration snapshot

## Status

Accepted for local architectural evidence.

## Decision

`build_execution_plan()` and `run_routed_pipeline()` accept an optional
`ConfigurationSnapshot`. When supplied, its canonical digest becomes the plan
configuration identity, the snapshot is retained in the `ExecutionPlan`, and a
conflict with the selected executor identity is rejected. The plan identity
includes the snapshot content, preventing two configurations with the same
task and treatment from silently collapsing into one plan.

## Falsifiable hypothesis and acceptance criteria

H1: a typed configuration snapshot supplied to orchestration survives into the
execution plan and cannot disagree with the executor identity.

- snapshot retained and digest propagated: PASS;
- identity mismatch rejected: PASS by `ExecutionPlan`/orchestration contract;
- deterministic local suite: 367 tests PASS;
- external qualification: not performed.

## Consequences

Configuration identity is no longer only an unstructured digest at the
orchestration boundary. Callers that have a canonical snapshot can preserve it
through planning and replay; legacy callers remain supported but have weaker
configuration evidence until they provide one.
