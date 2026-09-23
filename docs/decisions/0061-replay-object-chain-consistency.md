# ADR 0061 — Replay references must match outcome objects

## Decision

`validate_outcome_chain()` cross-checks a replayed `ReplayChain` against the
actual `VerificationResult`, `AcceptanceResult`, and `PromotionDecision`
objects. It requires:

- replay verification reference equals the verification result reference;
- replay acceptance reference equals the acceptance result reference;
- replay promotion reference equals the promotion decision reference;
- acceptance carries the exact verification reference;
- promotion carries the exact acceptance reference.

Reference presence alone is insufficient for chain integrity.

## Falsifiable hypothesis

A chain with complete but mismatched references is rejected, while a chain
whose references identify the supplied objects is accepted without executing
any external component. Tests falsify this if object drift passes validation.

## Acceptance evidence

The complete local suite ran 308 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests cover a valid causal chain and verification-reference
drift.

## Status

Accepted for replay and audit integrity. No external execution or promotion is
performed by this validator.
