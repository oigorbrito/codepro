# ADR 0071 — Routing policy must respect capability provenance

## Decision

`assess_capability_policy()` authorizes a capability only when:

- the adapter preflight is `READY`;
- a capability identity digest is present;
- all required capabilities are present;
- the observed provenance meets the policy minimum.

The provenance order is `DECLARED < OBSERVED < QUALIFIED`. A failed or blocked
preflight returns a policy denial, not an executor switch or fallback route.
This function authorizes capability use only; it does not choose or execute an
adapter.

## Falsifiable hypothesis

A declared-only capability cannot satisfy an observed/qualified policy, and a
blocked preflight cannot authorize routing. An observed capability satisfies an
observed minimum when identity and required names match. Tests falsify this if
policy silently upgrades provenance or selects a fallback.

## Acceptance evidence

The complete local suite ran 321 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests cover provenance insufficiency, blocked preflight, and
successful observed-capability authorization.

## Status

Accepted for routing policy. No executor/provider is selected or qualified by
this policy function alone.
