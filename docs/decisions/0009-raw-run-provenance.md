# ADR 0009 — Bind every raw run to immutable provenance

## Status

Accepted for the Arkx experimental chassis.

## Observed need

The frozen Study Spec defines a study before execution, but the existing P0 execution record does not by itself bind each observation to the exact study reference, Arkx commit, workload object, configuration, executor version, environment, repetition, and retained raw artifact.

Without that binding, later aggregation can become irreproducible or mix non-equivalent runs.

## Decision

Add a small independent Run Manifest contract. It is validated fail-closed and content-addressed. It records provenance only and does not duplicate acceptance semantics from P0 or P5.

Every analyzed observation must retain an individual raw execution record and a valid Run Manifest.

## Alternatives considered

- Add all fields directly to P0 `ExecutionRecord`: deferred to avoid coupling runtime telemetry to research-only metadata.
- Keep provenance only in CI logs: rejected because logs are insufficient as a stable per-observation analysis contract.
- Persist only summary statistics: rejected because raw observations are required for reproducible offline analysis.

## Limitation

The manifest validates syntax and completeness of declared provenance. It does not independently prove that an external reference existed at a particular time; chronology remains an evidence obligation tied to immutable repository/object history.

## Rollback/removal condition

Replace this contract if a future experiment harness provides an equally explicit or stronger one-to-one binding between frozen design, raw observation, configuration, environment, and immutable evidence.
