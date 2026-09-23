# Decision 0019 — P8.2 baseline executor adapter

## Status

Accepted as the fourth architecture strengthening block.

## Decision

Expose the existing P8.2 baseline runner through a thin
`P82BaselineExecutorAdapter`. The adapter translates the legacy
`ExecutionArtifact` into the neutral `ExecutionResult` contract and rejects a
request for a task different from the bound task.

The legacy runner remains available for compatibility. This adapter does not
qualify mini-SWE-agent, OpenRouter, Docker or SWE-bench.

## Falsifiable hypothesis

If the adapter translates one fixed baseline path without changing its input
identity or terminal state, then the neutral execution contract can be tested
against the real integration boundary before selecting another executor.

## Acceptance criteria

- completed baseline maps to neutral `COMPLETED`;
- blocked and failed artifacts preserve their error envelope;
- wrong task identity is rejected;
- existing runner tests remain passing;
- no real provider or executor qualification is claimed.
