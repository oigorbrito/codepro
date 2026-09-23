# ADR 0046 — Persistible recovery-plan lineage

## Decision

Arkx adds `RecoveryPlan`, derived deterministically from a `RecoveryDecision`
and a non-empty source `attempt_id`. The plan records action, reasons, current
path, and target path without executing the action.

Recovery planning remains separate from executor selection, retry execution,
handoff, verification, acceptance, and promotion.

## Acceptance

Equivalent inputs produce the same plan identity and serialization; the source
attempt is retained; and plan construction performs no external calls.
