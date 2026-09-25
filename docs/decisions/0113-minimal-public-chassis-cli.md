# Decision 0113 — Minimal public chassis CLI

## Status

Proposed for G3 pre-executor validation.

## Context

The packaged audit line had no public command. The previous fake-executor CLI
was based on a different module graph and could not be cherry-picked. The
current line already has a deterministic no-network baseline fixture, so the
first public boundary should expose only package health and that fixture.

## Decision

The `codepro` entrypoint exposes only:

- `codepro --version`;
- `codepro doctor [--json]`;
- `codepro baseline`.

It does not submit tasks, choose executors, invoke providers, perform fallback,
or claim product execution readiness.

## Falsifiable hypothesis and acceptance criteria

H1: After clean installation from wheel and sdist, the three commands are
available without `PYTHONPATH`; `doctor` reports the supported Python range and
`baseline` emits the existing deterministic PASS record.

Acceptance requires CLI tests, clean wheel and sdist invocations, exact
version identity, and independent acceptance. Unsupported Python must return a
nonzero status. Any executor invocation or hidden fallback is a failure.

## Removal condition

Replace this boundary only when a wider user-facing task contract is defined
and independently accepted; do not expand it implicitly to accommodate an
executor.
