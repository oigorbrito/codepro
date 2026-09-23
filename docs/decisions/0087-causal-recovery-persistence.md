# ADR 0087: Recovery persistence requires a recorded source execution

## Status

Accepted for local architectural evidence; recovery execution remains explicit.

## Decision

`append_recovery_plan()` persists a recovery stage only when the plan's source
attempt identity exactly matches an execution reference already present in the
same event log. The recovery action is retained as data. Persisting recovery
does not execute a replan, switch executors, or imply promotion.

## Falsifiable hypothesis and acceptance criteria

H1: a recovery artifact cannot float free of the attempt it claims to recover.
The focused test must accept a matching execution and reject a mismatched
execution reference.

## Consequences

Recovery is now replay-auditable at the persistence boundary. Full recovery
resume and replan execution remain future work and must use this causal record.
