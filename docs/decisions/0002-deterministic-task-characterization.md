# 0002 — Deterministic task characterization

- Status: executed with synthetic fixtures
- Date: 2026-09-22

## Context

P0 made execution measurement observable. The next safe increment is a deterministic structural hypothesis before execution, without giving the system authority to route or select an executor.

## Decision

Use explicit `TaskSignals`, closed enums, centralized conservative thresholds, structured reason codes, and fail-closed output. Preserve the input and derived evidence in a deterministic JSON record. Keep characterization independent from P0 execution status.

## Consequences

- Same semantic signals serialize identically after normalization.
- Missing or contradictory signals require qualification.
- Synthetic fixtures demonstrate contract stability only; they do not establish accuracy.
- No executor, router, planner, retry policy, replan policy, or model dependency is introduced.

## Revisit when

Real task evidence justifies validating or revising thresholds, adding richer signals, or designing P2 progress/stagnation measurement.

