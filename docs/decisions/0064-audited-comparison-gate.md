# ADR 0064 — Decision-grade comparison requires complete audited chains

## Decision

`AttemptStore.compare_audited()` loads and audits both attempts before applying
manifest comparability. If either restored chain is not `COMPLETE`, the method
fails explicitly instead of returning a comparison that could support
acceptance or promotion.

The existing `compare_attempts()` and `compare_attempt_collection()` functions
remain available for lower-level identity diagnostics. They must not be
interpreted as proof that verification, acceptance, or promotion evidence is
complete.

## Falsifiable hypothesis

An attempt pair with an incomplete or inconsistent persisted chain cannot pass
the decision-grade comparison gate, while legacy identity comparison remains
available. Tests falsify this if an incomplete chain is returned as eligible
for decision use.

## Acceptance evidence

The complete local suite ran 312 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests verify that incomplete audited chains are rejected.

## Status

Accepted for integrity-sensitive comparison. No external candidate is
accepted or promoted by comparison alone.
