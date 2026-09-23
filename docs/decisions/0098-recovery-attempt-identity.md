# ADR 0098: Restart and replan create a new attempt identity

## Status

Accepted for local architectural evidence.

## Decision

`RecoveryAttemptPlan` derives the next attempt id from trial id, consecutive
attempt number and configuration digest, while retaining the source attempt
and recovery reference. It is declarative only: it does not reserve a
directory, invoke an executor, switch provider, or select a treatment.

## Falsifiable hypothesis and acceptance criteria

H1: recovery cannot silently reuse the source attempt. Tests must derive a
different next identity and reject a source id that does not match lineage.

## Consequences

Artifact reservation and execution of the new attempt remain separate gates,
which preserves idempotency and prevents a replay operation from becoming a
hidden retry.
