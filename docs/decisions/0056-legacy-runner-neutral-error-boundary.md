# ADR 0056 — Legacy runner emits neutral error boundaries

## Decision

The P8.2 baseline runner retains its legacy `RunnerFailureCategory` in the
execution artifact, but its public manifest error is produced through the
neutral integration boundary where appropriate:

- missing identity remains a `HARNESS` precondition failure;
- environment and process-start failures are `SANDBOX` process failures;
- model, agent, timeout, capture, and run failures are `EXECUTOR` process
  failures;
- provider availability keeps its explicit bounded-retry policy and remains a
  `PROVIDER` error.

This preserves historical artifact meaning while preventing upper layers from
depending on runner-specific categories for domain routing.

## Falsifiable hypothesis

Equivalent legacy runner outcomes produce the same neutral domain and retain
raw artifact references, while missing identity does not become an executor
failure and provider retryability is not weakened. Tests falsify this if the
domain changes across equivalent outcomes or if legacy artifacts lose their
category.

## Acceptance evidence

The complete local suite ran 301 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Existing baseline tests for missing identity, provider
availability, execution failure, and artifact persistence passed.

This local result does not qualify the mini-SWE-agent provider, sandbox, or
SWE-bench evaluator.

## Status

Accepted for compatibility-preserving boundary migration. No external adapter
is promoted.
