# ADR 0017 — Record protocol deviations as first-class evidence

## Status

Accepted for the Arkx empirical chassis.

## Observed need

The project contract prohibits silent fallback, executor switching, and scope expansion. Run manifests can mention deviations, but free-text mentions alone do not capture before/after state, timing, evidence, or impact on confirmatory analysis.

## Decision

Add Protocol Deviation v1 as a structured, content-addressed record.

Behavior-affecting changes after freeze must identify the frozen value and observed value, evidence, phase, preauthorization status, and analysis impact. Unplanned high-risk deviations cannot claim no primary effect by default.

A material treatment-identity change can require a new frozen Study Spec rather than being treated as another repetition of the original study.

## Alternatives considered

- Put deviations only in logs: rejected because logs do not create stable analysis semantics.
- Ignore deviations that improve completion: rejected because outcome-dependent protocol changes bias comparison.
- Automatically invalidate every deviation: rejected because some preauthorized or non-primary changes can be handled transparently through the frozen Analysis Plan.

## Limitation

The record makes deviations explicit; expert judgment is still needed to determine their substantive impact. That judgment must be documented rather than hidden.

## Rollback/removal condition

Replace this contract if a future experiment harness natively records equivalent before/after protocol state and analysis consequences.
