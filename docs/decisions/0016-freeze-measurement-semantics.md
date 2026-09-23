# ADR 0016 — Freeze metric operational definitions

## Status

Accepted for the Arkx empirical chassis.

## Observed need

Study Spec v1 freezes metric names and the Validity Plan maps them to constructs, but neither alone prevents the operational meaning of a metric from changing between runs or analyses.

## Decision

Add Measurement Contract v1. Every study metric receives a frozen data type, unit, source, measurement rule, missing/invalid semantics, direction, and precision rule.

Missing or unknown measurements remain distinct from observed zero values.

## Alternatives considered

- Rely only on metric names: rejected because names such as "success", "cost", and "latency" admit multiple operational definitions.
- Put operational definitions in analysis code: rejected because implementation could drift after results are observed.
- Encode construct validity in the same object: rejected to preserve separation between measurement mechanics and interpretive validity.

## Limitation

The contract makes measurement semantics explicit; it does not guarantee that the underlying source is accurate or that the metric validly represents the intended construct.

## Rollback/removal condition

Replace this contract if a benchmark-native metric schema provides equivalent operational semantics and can be immutably referenced.
