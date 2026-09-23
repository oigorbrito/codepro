# ADR 0059 — Promotion requires a causal verification-to-acceptance chain

## Decision

Independent acceptance now records the deterministic `verification://`
reference alongside its evidence. The outcome promotion entrypoint requires
that same verification reference to be present in the acceptance evidence
before evaluating promotion policy.

Promotion therefore consumes a completed verification outcome, an acceptance
decision from the declared authority, and explicit evidence. Missing or
unlinked verification blocks promotion; it cannot be repaired by adding an
unrelated experiment or artifact reference.

The legacy `VerificationEvidence` path remains available for compatibility, but
new outcome-based callers should use `decide_outcome_promotion`.

## Falsifiable hypothesis

Acceptance without the exact verification reference is rejected by the
promotion gate, while a matching accepted outcome can be promoted only when
all existing evidence and authority policy requirements also pass. Tests
falsify this if an unlinked acceptance is promoted or if a linked non-pass
verification is promoted.

## Acceptance evidence

The complete local suite ran 304 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests cover verification reference propagation, mismatch
blocking, matching promotion, and preservation of the legacy promotion path.

## Status

Accepted for causal outcome-chain development. No external candidate is
promoted by this local evidence.
