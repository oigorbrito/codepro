# ADR 0088: Canonical secret-safe configuration snapshots

## Status

Accepted for local architectural evidence.

## Decision

`ConfigurationSnapshot` is the neutral representation for reproducible
configuration identity. It records component, version, public values and
digests of secret values, never secret material. Its canonical JSON and digest
are deterministic and can populate existing `configuration_digest` fields.

## Falsifiable hypothesis and acceptance criteria

H1: equivalent configuration mappings produce the same identity, while public
configuration or secret digests changing produce different identities. Tests
must cover canonical ordering, secret non-serialization and invalid identity.

## Scope boundary

This contract does not resolve configuration from environment variables or
secret stores. Adapters remain responsible for producing the snapshot and
recording the external resolver identity.
