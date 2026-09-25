# Decision 0164: CodePro event-log contract v1

**Status:** normative v1.1 contract; implementation under predecessor review
**Date:** 2026-09-25
**Contract version:** 1.1
**Normative decision:** true
**Derived only from precedent:** false

The product identity is CodePro. The current Python distribution uses the
compatibility package namespace `arkx`; package renaming is out of scope. The
implementation path is therefore `src/arkx/event_log.py`.

## Contract v1

Each event contains `sequence`, `event_type`, `payload`, `previous_digest`,
and `digest`. Sequences start at zero, are strictly contiguous, and match
physical order. The first event has a null `previous_digest`; each later event
references the preceding digest.

The digest is SHA-256 over canonical UTF-8 JSON using `sort_keys=true`,
`separators=(",", ":")`, and `ensure_ascii=false`, covering `sequence`,
`event_type`, `payload`, and `previous_digest`, while excluding `digest`.

`ChainIntegrity` has exactly `COMPLETE`, `EMPTY`, `INVALID`, and `TAMPERED`.
Zero events produce `EMPTY`, never `COMPLETE`. Schema, ordering, sequence, and
file-load failures are `INVALID`; digest or predecessor-link failures are
`TAMPERED`.

The exception taxonomy is `EventLogError`,
`EventLogFormatError(EventLogError)`, and
`EventLogIntegrityError(EventLogError)`. `ReplayAudit` exposes only the
consumer-required identity fields, `integrity`, and `chain`. `EventChain`
contains an ordered immutable event sequence and deterministic `to_dict()`
with `events`, `event_count`, and `head_digest`.

`audit_restored_chain(event_log_path, snapshot, outcomes=None)` loads events,
validates schema and ordering, recalculates hashes, validates links, builds the
chain, and returns the audit. It returns `COMPLETE` only when all checks pass.
There is no silent fallback or executor switch; `EMPTY`, `INVALID`, and
`TAMPERED` are never `COMPLETE`.

Contract v1.1 additionally exposes only `verification_ref`, `acceptance_ref`,
and `promotion_ref` in `EventChain.to_dict()`. Each value is derived from the
corresponding stage event's non-empty `ref`; an absent stage is represented as
`null`. A consumer that requires an absent reference fails closed. No fallback
or inferred reference is permitted.

No package rename, PR48 modification, PR48 merge, or promotion is authorized.
