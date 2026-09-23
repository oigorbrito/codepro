# ADR 0091: Providers require versioned configuration-bound identity

## Status

Accepted for local architectural evidence.

## Decision

The neutral `Provider` protocol exposes `provider_identity` as an
`AdapterIdentity` with `IntegrationKind.PROVIDER`. `validate_provider_identity`
rejects anonymous providers and providers lacking version or configuration
digest. The provider identity is separate from the model fields in
`ProviderRequest`.

## Falsifiable hypothesis and acceptance criteria

H1: a provider cannot enter the neutral contract without reproducible identity.
Tests must accept the versioned fake provider and reject an anonymous provider.

## Boundary

This does not qualify provider behavior, model quality, pricing, latency, or
availability. Those remain preflight and experimental evidence concerns.
