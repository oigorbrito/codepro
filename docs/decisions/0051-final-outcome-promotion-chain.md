# ADR 0051 — Final outcome-to-promotion chain validation

## Decision

`PromotionDecision.reference` is a deterministic `promotion://` identity.
`validate_final_chain` requires promotion to match the exact attempt and
decision, and requires an attached acceptance outcome to match its reference.
Verification and acceptance references remain independently supplied.

This validator checks lineage only; it does not promote a candidate or replace
the existing promotion policy.

## Acceptance

Matching final references pass; attempt, promotion, or acceptance drift fails;
no promotion side effect occurs during validation.
