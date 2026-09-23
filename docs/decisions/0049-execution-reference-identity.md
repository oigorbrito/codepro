# ADR 0049 — Canonical execution-chain references

## Decision

`ExecutionPlan.reference` returns `plan://<plan_id>`, while
`execution_reference(attempt_id)` returns `execution://<attempt_id>`.
`validate_execution_chain` requires both references to match the plan and exact
attempt identity.

This validates lineage only. It does not infer execution success from an
artifact reference or perform verification, acceptance, or promotion.

## Acceptance

Matching plan/attempt references pass; plan or attempt drift fails; no external
component is invoked.
