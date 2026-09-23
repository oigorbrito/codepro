# Decision 0015 — Promotion requires independent verification

## Status

Accepted.

## Evidence

The previous promotion contract required an accepted `AcceptanceResult` and
promotion evidence references, but did not require a separate verification
record. That allowed a caller to present acceptance without proving that an
independent verifier had evaluated the produced artifact.

## Decision

The default promotion policy requires independent `VerificationEvidence` with
state `PASS` and at least one raw evidence reference. Verification remains
separate from executor completion and acceptance authority.

## Falsifiable hypothesis

If promotion requires explicit verification evidence, then executor completion
or acceptance alone cannot produce `PROMOTED`.

## Acceptance criteria

- missing verification is `BLOCKED`;
- verification without evidence is `BLOCKED`;
- verification `INDETERMINATE` is never promoted;
- accepted candidates with valid verification and evidence preserve existing
  promotion behavior;
- snapshot promotion rejects non-completed executions and configuration
  identity mismatches;
- focused promotion and harness tests pass.
