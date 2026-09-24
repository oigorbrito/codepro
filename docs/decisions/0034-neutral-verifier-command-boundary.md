# Decision 0034 — Neutral verifier command boundary

## Status

Implemented as a local contract; not yet the MVP end-to-end path.

## Decision

The chassi provides one small verifier boundary that runs a declared argv in an
existing workspace with `shell=False`, a positive timeout, captured stdout and
stderr, exit code, duration and explicit environment errors.

It does not select an executor, interpret provider output, accept a task, or
persist a release decision. The caller remains responsible for atomic evidence
storage and independent acceptance.

## Falsifiable criteria

- exit code zero becomes `PASSED`;
- nonzero exit becomes `FAILED`;
- timeout, missing executable and invocation errors become `UNKNOWN` with an
  explicit error kind;
- invalid command or workspace is rejected before invocation;
- shell interpretation is never enabled.
