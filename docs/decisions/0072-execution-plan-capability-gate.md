# ADR 0072 — Execution plans carry and validate capability requirements

## Decision

`ExecutionPlan` records required capability names and a minimum capability
provenance. `ExecutionPlan.validate_capabilities()` applies the neutral routing
policy against an adapter preflight before execution.

A plan may be structurally valid while still being unauthorized to execute if
its preflight is blocked, its capability identity is absent, a required
capability is missing, or its provenance is below policy. Plan construction does
not select a fallback or invoke an executor.

## Falsifiable hypothesis

A declared-only capability cannot satisfy a plan requiring observed capability,
while the same plan can be authorized after an observed preflight with matching
identity and capability. Tests falsify this if plan validation silently upgrades
provenance or executes an adapter.

## Acceptance evidence

The complete local suite ran 322 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests cover capability requirements carried by a plan and
denial before execution when provenance is insufficient.

## Status

Accepted for execution-plan gating. No executor or provider is selected by plan
validation alone.
