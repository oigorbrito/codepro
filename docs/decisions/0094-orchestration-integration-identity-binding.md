# ADR 0094: Orchestration accepts explicit provider and sandbox bindings

## Status

Accepted for local architectural evidence.

## Decision

`build_execution_plan()` and `run_routed_pipeline()` accept optional provider
and sandbox identities. They are passed into the plan and validated there.
Omitting them preserves legacy compatibility but does not invent identities or
select defaults.

## Falsifiable hypothesis and acceptance criteria

H1: identities supplied to orchestration are present on the exact plan that is
executed. The focused test must compare both identity objects after pipeline
construction.

## Consequences

Concrete callers can bind qualified integrations before execution. Provider and
sandbox selection remains outside orchestration, and missing identities remain
observable as a qualification/reproducibility weakness.
