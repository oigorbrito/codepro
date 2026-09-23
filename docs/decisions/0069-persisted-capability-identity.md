# ADR 0069 — Persist capability identity without inferring capability quality

## Decision

`CapabilityRegistry` now exposes a deterministic digest and a
`capability://` reference derived from its canonical JSON representation. Strict
replay audit can observe and validate `capability_digest`; audited experiments
must record the same digest in their identity and event chain.

This contract establishes identity and consistency only. It does not assert
that a declared capability works, that an adapter is ready, or that a provider
is qualified. Those claims still require preflight and independent empirical
evidence.

## Falsifiable hypothesis

Equivalent registries produce the same digest, registry changes produce a
different digest, and an audited experiment with capability drift is rejected.
Tests falsify this if capability identity changes are invisible or if digest
presence is treated as functional qualification.

## Acceptance evidence

The complete local suite ran 317 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests cover deterministic registry identity and its
experiment/replay consistency boundary.

## Status

Accepted for capability identity persistence. Capability effectiveness remains
unqualified until empirical preflight/evaluation evidence exists.
