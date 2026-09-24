# ADR 0019 — Harden P4-P6 empirical semantics

## Status

Accepted for the Arkx empirical chassis.

## Observed need

The existing P4-P6 contracts were deterministic but contained three avoidable semantic hazards:

1. P5 serialized a post-patch boolean as `reproduction_passed_after_patch`, even though the successful fixed state was represented by `False`.
2. P4's generic plan builder could accept steps already marked completed, allowing plan creation to imply execution.
3. P6 deduplicated executor transition pairs, so repeated transitions could be undercounted against the transition budget.

## Decision

Break compatibility rather than preserve ambiguous aliases.

P5 schema v2 uses explicit before/after issue-reproduction semantics. P4 schema v2 rejects progress assertions during plan creation and strengthens replan evidence/budget checks. P6 schema v2 counts actual transition events, rejects duplicate handoff IDs, and validates nonnegative measurements.

## Alternatives considered

- Keep backward-compatible aliases: rejected because they preserve ambiguous empirical semantics.
- Fix only documentation: rejected because the ambiguous behavior was executable.
- Treat repeated transition pairs as one logical transition: rejected because budget and context cost are event-level observations.

## Limitation

These contracts still operate on declared structural inputs. They do not independently prove that a test, handoff, or plan observation is truthful; evidence provenance remains a separate obligation.

## Rollback/removal condition

Only replace these semantics with contracts that preserve the same directionality, no-progress-by-assertion rule, and event-count accounting.
