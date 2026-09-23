# ADR 0027 — Evidence-bearing capability profile registry

## Decision

Arkx gains a small neutral contract for runtime capabilities. A
`CapabilityProfile` records component type and identity, optional version and
configuration digest, declared capabilities, and evidence references.
`CapabilityRegistry` provides deterministic ordering and identity-safe lookup.

The registry is descriptive only in this phase. It does not discover runtime
capabilities, select an executor, perform fallback, or qualify a provider.

## Rationale

Executor selection already had string capabilities, while provider and sandbox
contracts exposed identity without a comparable evidence-bearing capability
boundary. This made capability claims difficult to compare or replay. The
contract makes identity and evidence explicit without coupling routing to a
specific provider or model.

## Falsifiable hypothesis and acceptance

For equivalent profile inputs, serialization and registry ordering are stable;
duplicate identities are rejected; lookup does not invoke external systems.
Acceptance requires deterministic unit tests. This is local contract evidence,
not qualification evidence.

## Non-goals

- dynamic discovery;
- capability inference from a model name;
- executor/provider fallback;
- promotion or benchmark claims.
