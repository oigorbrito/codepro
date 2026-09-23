# 0013 — Core verification and acceptance outcome boundary

## Status

Accepted for implementation as a compatibility-preserving refactoring.

## Problem

`acceptance`, `promotion`, and `orchestration` currently import
`VerificationResult`, `AcceptanceResult`, and their state enums from
`p82_baseline`.  This makes executor-neutral product boundaries depend on the
Treatment A experimental runner.

## Decision

Move the shared verification and acceptance outcome types to an executor-neutral
core module.  The baseline module may re-export them temporarily for backwards
compatibility, but core modules must no longer import from `p82_baseline`.

## Falsifiable hypothesis

If shared outcome types are moved to a neutral module without changing their
serialized shape or semantics, all existing deterministic contract tests will
continue to pass and core modules will no longer have a baseline-runner import
dependency.

## Acceptance criteria

1. Existing outcome constructors and `to_dict()` output remain compatible.
2. `acceptance`, `promotion`, and `orchestration` import only the neutral core
   outcome module.
3. Existing tests pass with the repository source path configured.
4. The baseline runner remains compatible through explicit re-exports.
5. No provider, model, executor, or sandbox behavior changes.

## Removal condition

Remove the compatibility re-exports only after downstream imports have been
migrated and a public API compatibility review has accepted the change.
