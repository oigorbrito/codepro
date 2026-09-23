# ADR 0052 — Common adapter qualification preflight

## Decision

Arkx adds a neutral preflight contract for executor, provider, sandbox, and
evaluator adapters. `AdapterIdentity` records kind, name, version, and
configuration digest. `DependencyObservation` records availability without
inference. `AdapterPreflight` records status, capabilities, dependencies,
evidence, and reason.

`assess_preflight` produces `READY`, `BLOCKED`, `UNKNOWN`, or `FAILED` without
loading or invoking a concrete adapter and without selecting a fallback.

`preflight_error` maps a non-ready preflight to the neutral `ErrorEnvelope`,
preserving the integration boundary, preflight reference, and
`Retryability.UNKNOWN`. It does not infer retryability from a missing
dependency or from an adapter's failure.

## Acceptance

Ready, blocked, unknown, and failed boundaries remain distinguishable;
equivalent observations serialize deterministically; and missing dependencies do
not become success. Error mapping preserves the boundary and raw evidence
reference without selecting a fallback.
