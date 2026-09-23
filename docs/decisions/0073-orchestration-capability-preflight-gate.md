# ADR 0073 — Orchestration must validate plan capabilities before execution

## Decision

`build_execution_plan()` carries the selected treatment's required
capabilities. `run_routed_pipeline()` accepts an optional concrete preflight and
checks the resulting plan before invoking `executor.run`.

If a plan requires capabilities and no preflight is supplied, orchestration
returns `CAPABILITY_PREFLIGHT_REQUIRED`. If the preflight does not satisfy the
capability policy, orchestration returns `CAPABILITY_POLICY_BLOCKED`. Neither
case selects a fallback executor.

Legacy plans with no capability requirements remain compatible; they do not
claim capability qualification merely because execution was invoked.

## Falsifiable hypothesis

A capability-requiring plan cannot invoke an executor without a qualifying
preflight, while a plan with no capability requirement preserves legacy
behavior. Tests falsify this if `executor.run` is called before the gate.

## Acceptance evidence

The complete local suite ran 323 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests verify required capabilities are carried into the plan
and missing preflight blocks orchestration before executor invocation.

## Status

Accepted for orchestration gating. No executor/provider is selected or
qualified by this gate alone.
