# ADR 0030 — Deterministic retry attempt lineage

## Decision

An authorized retry produces a `RetryAttemptPlan` with a new deterministic
attempt identity derived from the same trial, the next attempt number, and the
configuration digest. The previous attempt identity is retained and validated.

The plan is only lineage metadata. It does not reserve a directory, overwrite
artifacts, invoke an executor, or claim that the retry succeeded.

## Acceptance

Equivalent retry inputs produce the same next attempt identity and serialized
plan. Unauthorized retry produces no plan. Inconsistent previous identity is
rejected. Artifact reservation remains an explicit later operation.
