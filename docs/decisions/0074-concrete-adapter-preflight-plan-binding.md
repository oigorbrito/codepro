# ADR 0074 — Concrete adapter preflight must bind to the execution plan

## Decision

`P82BaselineExecutorAdapter.preflight()` returns an executor-scoped
`AdapterPreflight` without invoking the runner. It records executor identity,
version, configuration digest, dependency availability, declared capability,
and capability provenance.

`ExecutionPlan.preflight_matches_identity()` requires the preflight to describe
the same executor kind, executor id, and configuration digest as the plan.
Orchestration rejects mismatched preflight before invoking the executor.

## Falsifiable hypothesis

A preflight from another executor or configuration cannot authorize a plan, and
preflight collection does not execute the runner. Tests falsify this if identity
drift passes or if preflight has execution side effects.

## Acceptance evidence

The complete local suite ran 325 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests cover P8.2 preflight identity, declared capability
provenance, and plan rejection of another executor's preflight.

The concrete dependency may still be unavailable; that state remains an
explicit preflight result and is not converted to a fallback.

## Status

Accepted for concrete adapter binding. No adapter is promoted by preflight
identity alone.
