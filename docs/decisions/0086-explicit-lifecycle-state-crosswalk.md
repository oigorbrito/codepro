# ADR 0086: Keep lifecycle vocabularies separate but crosswalked explicitly

## Status

Accepted for local architectural evidence.

## Decision

`RunState` remains the execution lifecycle vocabulary. `ExecutionOutcome` is
the neutral adapter boundary, and `OrchestrationStatus` is the composed result
vocabulary that also includes verification and acceptance. Their meanings are
not collapsed. Total pure crosswalk functions are public and tested so mapping
drift cannot be hidden in ad-hoc dictionaries inside the pipeline.

## Falsifiable hypothesis and acceptance criteria

H1: every execution outcome and acceptance decision maps deterministically to
exactly one orchestration status. The crosswalk test must cover every enum
member.

## Rationale

Creating a third universal state machine now would duplicate semantics. The
explicit crosswalk is the smallest evidence-backed correction while recovery
and crash-resume semantics are still being designed.
