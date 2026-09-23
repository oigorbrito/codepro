# ADR 0015 — Freeze complete treatment configuration

## Status

Accepted for the Arkx empirical chassis.

## Observed need

Run provenance already contains a `configuration_ref`, but without a versioned configuration contract that reference can hide changes in prompts, model/provider identity, tools, parameters, attempts, timeouts, fallback, or seeding.

## Decision

Add Treatment Configuration Manifest v1. Any behavior-affecting configuration change creates a distinct content identity.

Provider/model revisions are recorded when available. When a provider does not expose an immutable model revision or deterministic seed, that limitation is explicit and must be handled through repetitions and validity analysis rather than hidden.

Fallback is disabled by default. If enabled for a study, every target must be frozen before execution.

## Alternatives considered

- Treat executor/model name as sufficient identity: rejected because substantial behavior can vary under the same label.
- Snapshot provider-hosted model weights: generally unavailable and outside Arkx control.
- Allow runtime fallback to improve completion rate: rejected as a default because it changes treatment assignment.

## Limitation

A frozen client configuration cannot prevent unannounced server-side provider changes. It makes the residual threat visible and attributable but does not eliminate it.

## Rollback/removal condition

Replace this contract if an executor-native immutable configuration artifact contains equivalent information and can be content-addressed directly.
