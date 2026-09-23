# ADR 0018 — Separate empirical eligibility from promotion

## Status

Accepted for the Arkx empirical chassis.

## Observed need

The project contract distinguishes acceptance from promotion, but a free-text promotion rule does not provide a deterministic fail-closed gate. A favorable result could otherwise be promoted without all predeclared evidence being present.

## Decision

Add Promotion Gate v1.

Criteria and required evidence are frozen before the final promotion assessment. Missing observations or evidence block the gate; failed criteria make the candidate ineligible. Satisfying every gate only produces `ELIGIBLE_FOR_REVIEW`.

Promotion itself remains an explicit later decision containing reviewer, rationale, and evidence references. The system refuses a promoted record when the gate is not eligible.

## Alternatives considered

- Auto-promote on PASS or verifier success: rejected because execution success is not an architectural decision.
- Leave promotion as free text only: rejected because missing evidence cannot be enforced fail-closed.
- Force promotion whenever the gate passes: rejected because residual validity or operational risk may justify non-promotion.

## Limitation

The gate enforces predeclared criteria but cannot guarantee that thresholds were substantively well chosen. Threshold justification remains part of study design and review.

## Rollback/removal condition

Replace this gate if a future governance mechanism provides equivalent deterministic eligibility and preserves an explicit independent promotion decision.
