# Decision 0034 — Neutral verifier command boundary

## Status

Implemented as a local contract; not yet the MVP end-to-end path.

## Decision

The chassi provides one small verifier boundary that runs a declared argv in an
existing workspace with `shell=False`, a positive timeout, captured stdout and
stderr, exit code, duration and explicit environment errors. A
`CommandVerifier` adapts that observation to the orchestration seam and
`VerificationEvidenceStore` persists the raw observation under the stable
`run_id`/test identity. Equivalent content is idempotent; divergent content
for the same identity is a collision and blocks verification.

It does not select an executor, interpret provider output, accept a task, or
persist a release decision. The verifier owns raw command evidence; the caller
still owns lifecycle/event-log persistence, independent acceptance and release
promotion.

## Falsifiable criteria

- exit code zero becomes `PASSED`;
- nonzero exit becomes `FAILED`;
- timeout, missing executable and invocation errors become `UNKNOWN` with an
  explicit error kind;
- invalid command or workspace is rejected before invocation;
- shell interpretation is never enabled.
- raw stdout/stderr and result metadata are persisted atomically;
- a second observation with divergent content for the same run/test identity
  becomes `BLOCKED`, never a silent overwrite.
