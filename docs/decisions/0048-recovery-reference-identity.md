# ADR 0048 — Canonical recovery-plan reference identity

## Decision

`RecoveryPlan.reference` returns the canonical `recovery://<plan_id>` reference.
`validate_recovery_reference` rejects replay or artifact references that do not
match the exact plan identity.

The validator does not execute, persist, hand off, or promote recovery.

## Acceptance

The canonical reference passes validation; a different plan reference fails;
equivalent plans retain the same reference.
