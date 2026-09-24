# ADR 0029: Promotion requires independent acceptance

## Status

Accepted for implementation in issue #8.

## Hypothesis

If a promotion record is bound to an independent acceptance decision and to
the exact component, paths, configuration, and study evidence being promoted,
then an eligible score or executor output cannot silently acquire tenure.

## Contract

`record_promotion_decision(..., promote=True)` requires an
`AcceptanceDecision` with status `ACCEPTED`, an acceptance record reference,
component reference, non-empty path references, configuration reference, and
study evidence references. The resulting `PromotionRecord` preserves these
bindings. Gate assessment remains canonical and promotion remains an explicit
human/reviewer decision; blocked or indeterminate inputs cannot be promoted.

## Falsifiable acceptance criteria

1. A gate that is eligible plus an accepted independent decision and complete
   scope/evidence bindings produces a promoted record containing those refs.
2. Missing acceptance or any non-`ACCEPTED` acceptance status raises before a
   promotion record is created.
3. Missing component/path/configuration/study references raises before
   promotion; no implicit tenure is created.
4. Existing gate hash and canonical assessment checks remain intact, and the
   focused and complete suites are recorded separately from upstream CI.
