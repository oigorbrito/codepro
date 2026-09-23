# ADR 0102: Recovery reservation consumes the persisted attempt budget

## Status

Accepted for local architectural evidence.

## Decision

`ArtifactStore.reserve_recovery_attempt()` optionally accepts the persisted
budget ledger. When present, the source attempt must be in the ledger and the
next attempt must remain within `max_attempts`. Budget exhaustion is rejected
before directory creation. A missing ledger remains a weaker legacy path and
must be qualified by the caller.

## Falsifiable hypothesis and acceptance criteria

H1: recovery cannot bypass a persisted attempts budget. The test must reject a
source with `max_attempts` already consumed and prove no directory was created.

## Consequences

The method validates budget state but does not mutate the ledger. The caller
must persist the updated ledger atomically as part of the new attempt's
manifest/lifecycle.
