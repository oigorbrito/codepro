# ADR 0029 — Explicit retry authorization policy

## Decision

Arkx adds `RetryPolicy` and `RetryDecision` at the neutral execution boundary.
The policy authorizes a retry only when the error is explicitly retryable, its
domain is allowed, the retry limit remains available, and the execution budget
allows the next attempt.

The policy is pure: it does not invoke an executor, sleep, mutate artifacts,
replace an executor, or perform recovery. Recovery remains responsible for
choosing a broader action such as replan, escalation, handoff, or block.

## Acceptance

Tests must distinguish retryable, non-retryable, unknown, disallowed-domain,
policy-exhausted, and budget-exhausted cases. No automatic retry is inferred
from a local test result.
