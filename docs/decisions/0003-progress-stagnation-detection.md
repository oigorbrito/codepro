# 0003 — Deterministic progress / stagnation detection

- Status: executed with synthetic fixtures
- Date: 2026-09-22

## Context

P0 measures execution and P1 characterizes task structure. P2 must make progress observable before any future policy receives authority to change execution.

## Decision

Compare normalized, explicit snapshots. Treat new useful evidence and reduced distances as progress. Treat repeated failure signatures without new evidence, or repeated actions with unchanged acceptance distance, as no progress. Return `UNKNOWN` for missing required measurements or contradictory distances.

## Consequences

- Snapshot set ordering does not affect assessment serialization.
- The detector is evidence-only and cannot produce `PASS`.
- Retry, replan, routing, executor selection, and escalation remain external concerns.
- No OpenHands dependency or copied donor framework is introduced; this is a local, smaller adaptation of the generic idea that repeated unchanged failure can indicate stagnation.

## Revisit when

Empirical runs provide evidence for validating thresholds, adding event integration, or designing a future policy outside P2.

