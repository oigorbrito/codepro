# ADR 0070 — Capability preflight records provenance without conflating qualification

## Decision

`AdapterPreflight` carries an optional capability digest and explicit
`CapabilityProvenance`: `DECLARED`, `OBSERVED`, or `QUALIFIED`.

- `DECLARED` identifies what a registry or adapter claims;
- `OBSERVED` identifies what a runtime preflight observed;
- `QUALIFIED` is permitted only when evidence references are present.

Preflight status and capability provenance are independent dimensions. A
`READY` preflight does not imply qualified capability, and a capability digest
does not prove effectiveness.

## Falsifiable hypothesis

Equivalent capability identity serializes deterministically, provenance survives
preflight serialization, and `QUALIFIED` without evidence is rejected. Tests
falsify this if declared capability becomes qualified by inference.

## Acceptance evidence

The complete local suite ran 318 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests cover capability digest/provenance transport and
evidence requirements for qualification claims.

## Status

Accepted for capability/preflight boundary development. No adapter capability
is qualified by this contract alone.
