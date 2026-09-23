# ADR 0067 — Strict reproducibility requires version-compatible replay events

## Decision

Restored-chain audits observe protocol and event schema versions from persisted
events. Historical logs without version metadata remain readable when no
expected version is requested. A strict audit with an expected protocol
requires every observed version to be present, homogeneous, and equal to the
expected `protocol_version` and supported event schema version.

Audited experiment validation additionally requires the audit protocol to match
the experiment protocol and requires explicit event schema metadata.

## Falsifiable hypothesis

Protocol or schema drift in a replayed chain is rejected for reproducibility,
while legacy logs remain readable for historical inspection. Tests falsify this
if mixed versions pass strict audit or if a strict experiment accepts an
unversioned chain.

## Acceptance evidence

The complete local suite ran 315 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests cover protocol drift rejection, schema presence for
audited experiments, and compatibility of unversioned historical replay.

## Status

Accepted for versioned replay compatibility. No benchmark or provider
qualification is inferred from schema agreement.
