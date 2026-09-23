# ADR 0058 — Evaluator results become verification outcomes before acceptance

## Decision

`OfficialEvaluationResult.verification_result()` converts the official
evaluator observation to the executor-neutral `VerificationResult` contract.
The mapping is explicit:

- `RESOLVED` → `PASS`;
- `TESTS_FAILED` → `FAIL`;
- infrastructure error or ambiguity → `INDETERMINATE`;
- not executed → `NOT_EXECUTED`;
- blocked → `BLOCKED`.

Authority, command identity, outcome text, and report/log evidence are carried
into the verification result. Acceptance remains a later policy decision and
promotion remains outside this method.

## Falsifiable hypothesis

Equivalent evaluator results produce deterministic verification references and
cannot produce a promotion decision. Tests falsify this if evaluator status is
lost, evidence is reordered nondeterministically, or acceptance/promotion is
implicitly performed during conversion.

## Acceptance evidence

The complete local suite ran 303 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. The evaluator tests verify status mapping, authority,
command identity, evidence, and the absence of implicit promotion.

## Status

Accepted for evaluator-to-verification integration. No provider, evaluator, or
promotion is qualified by local tests.
