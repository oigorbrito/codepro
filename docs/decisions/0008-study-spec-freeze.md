# ADR 0008 — Freeze empirical study design before execution

## Status

Accepted for the Arkx experimental chassis.

## Observed need

P0-P6 provide deterministic contracts, telemetry, policy boundaries, verification, and handoff accounting, but they do not themselves prevent a researcher from selecting a workload, metric, comparator, stopping rule, or promotion criterion after seeing results.

That leaves a low-cost but material threat to conclusion validity and reproducibility.

## Decision

Add a minimal, executable Study Spec v1 above P0-P6.

A Study Spec must define the research question, falsifiable hypothesis, methodology, experimental unit, workload, quality attribute, metrics, comparison design, repetitions, stopping rule, analysis-plan reference, promotion rule, environment reference, and raw-results policy.

The spec is validated fail-closed and content-addressed before execution. Real runs must also reference an immutable repository/object identity that existed before execution.

## Alternatives considered

- Documentation-only template: rejected because required fields could drift without executable validation.
- Full experiment-management framework: rejected as premature architecture.
- Content hash as preregistration proof: rejected because a hash proves integrity but not temporal precedence.

## Evidence and limitation

This contract improves design traceability and prevents several classes of silent post-hoc change. It does not establish that a selected benchmark is representative, that metrics have construct validity, or that the statistical analysis is appropriate. Those remain separate evidence obligations.

## Rollback/removal condition

Remove or replace this contract if a smaller mechanism provides equivalent fail-closed pre-execution design guarantees, or if a future experiment harness subsumes it without weakening state separation.
