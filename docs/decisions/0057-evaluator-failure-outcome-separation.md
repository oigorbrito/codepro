# ADR 0057 — Evaluator failures remain separate from verification outcomes

## Decision

`OfficialEvaluationResult` exposes `error_envelope()` only for evaluator
states that do not represent a completed test verdict. Infrastructure errors,
ambiguous reports, blocked runs, and non-execution map to the neutral
`VERIFICATION` domain with an `EVALUATOR_<STATUS>` code and preserved report/log
references.

`RESOLVED` and `TESTS_FAILED` do not produce an error envelope. The former is a
completed positive evaluator outcome; the latter is a completed negative test
outcome. Both remain available to the separate acceptance mapping.

## Falsifiable hypothesis

An evaluator infrastructure failure cannot be mistaken for a test failure, and
a completed test failure cannot be retried merely because it is negative. Tests
falsify this if the two statuses produce the same error representation or if
raw evaluator evidence is lost.

## Acceptance evidence

The complete local suite ran 302 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests verify the distinction between infrastructure error and
`TESTS_FAILED`, including domain, stable code, retryability, and report/log
references.

Docker/SWE-bench execution remains externally blocked and is not qualified by
this local contract evidence.

## Status

Accepted for evaluator/verification boundary development. No promotion occurs.
