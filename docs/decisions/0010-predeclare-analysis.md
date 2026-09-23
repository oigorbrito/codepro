# ADR 0010 — Predeclare analysis before inspecting outcomes

## Status

Accepted for the Arkx empirical chassis.

## Observed need

A frozen Study Spec prevents post-hoc changes to workload, metrics, repetitions, and comparison design, but it does not fully prevent selecting estimands, missing-data handling, outlier rules, confidence procedures, or multiplicity treatment after observing results.

## Decision

Introduce an independent Analysis Plan v1. It is frozen before confirmatory analysis and must be compatible with the governing Study Spec.

The plan declares the estimand, analysis design, summaries, inference mode, uncertainty method, analysis population, and explicit rules for missing, blocked, deviating, multiple, and outlying observations.

## Alternatives considered

- Hard-code one statistical test into Arkx: rejected because the appropriate analysis depends on study design and data characteristics.
- Allow the analysis script alone to define methodology: rejected because code can change after results are visible without a separate predeclared contract.
- Treat every metric as confirmatory: rejected because this increases researcher degrees of freedom and multiplicity risk.

## Limitation

The contract validates declared intent and compatibility, not statistical correctness. A technically valid plan can still choose an inappropriate estimator or uncertainty method; that must be reviewed against the actual study design and established statistical guidance.

## Rollback/removal condition

Replace this contract if a future analysis harness provides equivalent or stronger pre-outcome specification and preserves explicit protocol-deviation semantics.
