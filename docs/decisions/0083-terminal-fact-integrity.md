# ADR 0083: Terminal facts are immutable and explicitly validated

## Status

Accepted for local architectural evidence; not an external qualification.

## Decision

`EventLog.append_terminal()` treats status and error code as one immutable
terminal identity. Repeating an identical terminal fact is idempotent; changing
either field is rejected. `validate_terminal_replay()` compares a replayed
terminal fact with an explicitly supplied expected status and optional error
code. A missing terminal event is an error, not an inferred success.

## Falsifiable hypothesis and acceptance criteria

H1: replay cannot silently change the terminal explanation while preserving the
same status. Tests must reject changed error codes, reject missing terminal
facts, reject wrong error codes, and accept an exact terminal match.

## Evidence

The focused tests and the complete local suite provide deterministic evidence.
This block does not qualify an executor, provider, model, Docker, or
SWE-bench authority.
