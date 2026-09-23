# ADR 0050 — Canonical verification and acceptance references

## Decision

`VerificationResult.reference` and `AcceptanceResult.reference` are stable
content-derived references with distinct namespaces. `validate_outcome_references`
requires each supplied reference to match its exact outcome.

Verification and acceptance remain independent; a matching reference does not
itself authorize promotion.

## Acceptance

Equivalent outcomes produce equal references, namespaces remain distinct, and
reference drift is rejected without external calls.
