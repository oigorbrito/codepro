# ADR 0066 — Reproducible experiment identity binds execution variables

## Decision

Arkx derives an `identity_digest` for an experiment from the ordered attempt
inventory and execution-relevant manifest fields: task and revision, treatment,
executor, provider, model, sandbox, repository revision, configuration digest,
budget digest, and protocol version.

The audited experiment validator requires this digest and rejects experiments
whose recorded identity differs from the loaded attempts. Historical records
may remain readable through the compatibility validator without making a
reproducibility claim.

## Falsifiable hypothesis

Changing any execution-relevant identity field changes the experiment digest,
while reordering attempts does not. An audited experiment with a missing or
drifted digest is rejected.

## Acceptance evidence

The complete local suite ran 314 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Existing experiment serialization and audited-validation
tests passed with the new optional identity field.

## Status

Accepted for reproducible experiment identity. No model, provider, executor, or
benchmark is qualified by digest computation alone.
