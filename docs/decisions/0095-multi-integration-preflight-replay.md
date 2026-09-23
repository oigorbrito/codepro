# ADR 0095: Persist separate preflight references for each bound integration

## Status

Accepted for local architectural evidence.

## Decision

Replay chains distinguish executor `preflight_ref`, `provider_preflight_ref`,
and `sandbox_preflight_ref`. Orchestration requires a matching READY preflight
for every provider or sandbox identity explicitly bound to the plan and
persists each reference before execution. Missing or mismatched preflights
block without choosing a default integration.

## Falsifiable hypothesis and acceptance criteria

H1: a multi-integration plan can be replayed without losing one preflight to
another. End-to-end tests must require the preflights and recover both distinct
references from the event log.

## Consequences

The event log has a small schema extension rather than overloading one generic
preflight slot. Existing executor-only chains remain compatible.
