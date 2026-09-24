# ADR 0027 — Explicit recovery controller

## Hypothesis

An explicit controller can connect progress, routing, replan, escalation, and
handoff decisions without silently selecting an executor or expanding scope.

## Contract

The controller consumes measured `ProgressAssessment`, `EvidenceSufficiency`,
and bounded routing budget state. It emits exactly one auditable action:
`CONTINUE`, `REPLAN`, `ESCALATE`, `HANDOFF`, or `BLOCK`.

`REPLAN` requires both the previous plan reference and the new plan reference.
`HANDOFF` requires an explicit target executor, evidence references, and a
within-budget handoff summary. Missing identity, evidence, or budget becomes
`BLOCK`; no fallback executor is selected.

## Acceptance criteria

The tests must falsify: progress continuation, no-progress escalation, missing
causal replan references, missing handoff evidence, exhausted handoff budget,
and a valid explicit handoff.
