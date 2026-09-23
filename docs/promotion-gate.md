# Promotion Gate v1

Empirical success and architectural promotion are separate decisions.

A Promotion Gate freezes the quantitative or categorical criteria and evidence requirements that make a result **eligible for review**. It does not automatically promote anything.

## Fail-closed evaluation

For every criterion:

- missing observation -> `BLOCKED`;
- malformed observation -> `BLOCKED`;
- criterion not satisfied -> `NOT_ELIGIBLE`;
- all criteria satisfied and all required evidence present -> `ELIGIBLE_FOR_REVIEW`.

`ELIGIBLE_FOR_REVIEW` still requires an explicit promotion or non-promotion decision with reviewer, rationale, and evidence references.

## Why this is separate

The Study Spec says that a promotion rule exists. The Promotion Gate makes that rule executable and immutable. The promotion record is a later governance decision based on the gate assessment and evidence.

## Boundary

```text
PASS != PROMOTED
VERIFIED != PROMOTED
STATISTICALLY_FAVORABLE != PROMOTED
ELIGIBLE_FOR_REVIEW != PROMOTED
MISSING_CRITERION != PASS
```
