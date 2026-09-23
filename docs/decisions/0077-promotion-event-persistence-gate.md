# ADR 0077 — Promotion persistence requires the preceding causal chain

## Decision

`append_promotion_decision()` persists a `promotion` stage only when the same
`EventLog` already contains the supplied verification reference and the
acceptance reference embedded in the `PromotionDecision`.

Promotion without persisted acceptance, acceptance from another chain, or
verification reference drift is rejected. The function records the promotion
decision reference and status but does not execute or mutate the candidate.

## Falsifiable hypothesis

A valid verification/acceptance/promotion chain replays all three references,
while promotion attempted before acceptance or with another acceptance fails.
Tests falsify this if a partial chain receives a promotion event.

## Acceptance evidence

The complete local suite ran 329 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests cover successful persistence and rejection of missing
or mismatched acceptance.

## Status

Accepted for promotion event persistence. This does not itself approve or
promote any external component.
