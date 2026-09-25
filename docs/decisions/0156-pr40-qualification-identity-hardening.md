# Decision 0156: qualification identity hardening

## Status

Validated as an isolated follow-up to PR40. Promotion is not authorized.

## Problem

The PR40 contract allowed a completed trial with missing executor or
environment identity to become `QUALIFIABLE` when an acceptance flag was
present.

## Decision

`assess_trial` now returns `UNKNOWN` when material control identity is absent:
executor version/configuration digest, task revision and acceptance
definition, model, or environment identity fields.

Paired validation records `IDENTITY_INCOMPLETE` instead of allowing the
missing identity to be treated as a controlled comparison.

## Evidence

The focused executor-qualification suite passed 19 tests on the clean
follow-up worktree. Two negative tests cover incomplete executor/environment
identity and paired-report classification.

This block does not change execution, provider, runtime, harness, routing,
fallback, or agent-loop behavior. It does not qualify an executor or authorize
promotion.
