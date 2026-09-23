# 0001 — Greenfield bootstrap

- Status: accepted for bootstrap
- Date: 2026-09-22

## Context

Arkx is the canonical new repository. The bootstrap must establish a durable contract without importing code, history, dependencies, issues, pull requests, or decisions from `smag-rex`.

## Decision

Start with documentation, empty structural boundaries, a dependency-free foundation check, and CI for that check. Keep runtime architecture and integrations out of scope until empirical evidence justifies them.

## Consequences

- The repository is intentionally not feature-complete after bootstrap.
- The invariants are reviewable and machine-checked for presence.
- Future changes must introduce their own evidence and decision records.
- No donor repository is a dependency of the product.

## P0 follow-up

P0 baseline telemetry is implemented, executed, and tested on a branch derived from this bootstrap:

```text
P0_TELEMETRY = IMPLEMENTED / EXECUTED / TESTED
P0_BASELINE_TELEMETRY = EXECUTED_WITH_SCOPE
```

It is not marked `ACCEPTED` or `PROMOTED` by this record.

## Revisit when

The first concrete capability has a reproducible hypothesis and a need for executable product code, experiment fixtures, or a runtime dependency.
