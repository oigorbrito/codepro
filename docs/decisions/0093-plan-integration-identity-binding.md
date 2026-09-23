# ADR 0093: Bind provider and sandbox identities to the execution plan

## Status

Accepted for local architectural evidence.

## Decision

`ExecutionPlan` may carry versioned `provider_identity` and `sandbox_identity`
objects. When present, each identity must have the correct integration kind,
version, configuration digest, and name matching the corresponding plan id.
Legacy plans without these identities remain readable but are weaker for
reproducibility and qualification.

## Falsifiable hypothesis and acceptance criteria

H1: a plan cannot bind a provider or sandbox identity from another component.
Tests must accept matching identities and reject an id mismatch.

## Consequences

The plan now provides one place to compare executor, provider and sandbox
identity. It does not select providers, start sandboxes, or qualify behavior.
