# ADR 0092: Sandboxes require versioned configuration-bound identity

## Status

Accepted for local architectural evidence.

## Decision

The neutral `Sandbox` protocol exposes `sandbox_identity` as an
`AdapterIdentity` with `IntegrationKind.SANDBOX`. The identity must include
version and configuration digest. `validate_sandbox_identity` rejects
anonymous or incomplete sandbox implementations.

## Falsifiable hypothesis and acceptance criteria

H1: a sandbox cannot enter the neutral contract without reproducible runtime
identity. Tests must accept the versioned fake sandbox and reject an anonymous
implementation.

## Boundary

Identity validation does not prove isolation, Docker correctness, filesystem
safety, or runtime availability. Those remain preflight and qualification
responsibilities.
