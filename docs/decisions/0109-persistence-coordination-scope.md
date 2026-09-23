# ADR 0109: Persistence coordination remains audit-based at current scope

## Status

Accepted for local architectural evidence.

## Decision

Arkx keeps atomic artifact writes plus an append-only event log as the current
single-process persistence boundary. It does not introduce a distributed event
bus, a multi-file transaction coordinator, or a database-backed lifecycle
store yet. Restored-chain audit and replay must detect missing, incomplete, or
inconsistent records and preserve them as non-success states.

## Evidence and falsifiable criteria

H1: a partial or divergent persisted lifecycle cannot be treated as a complete
accepted attempt without a new transaction subsystem.

- atomic manifest/artifact writes are exercised: PASS;
- missing and indeterminate chain references are classified: PASS;
- replay/manifest and outcome drift are rejected: PASS;
- full deterministic suite: 367 tests PASS;
- multi-writer/distributed execution: NOT IN SCOPE and not qualified.

## Rationale

The current harness is local and serial. A transaction coordinator or event bus
would add failure modes and operational surface without an empirical consumer
requiring fan-out or concurrent writers. The decision can be revisited when
parallel workers, remote artifact stores, or distributed lifecycle consumers
are introduced.

## Consequences

Persistence is crash-detecting rather than crash-atomic across independent
files. A restored attempt with incomplete evidence is blocked or indeterminate;
it is never repaired or promoted by inference.
