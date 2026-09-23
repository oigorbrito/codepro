# Decision 0021 — Direct neutral executor orchestration

## Status

Accepted as the sixth architecture strengthening block.

## Decision

The routed orchestration entrypoint accepts the neutral `Executor` protocol
directly. The legacy `ExecutorRunner` result shape remains a compatibility
boundary, but new callers do not need to know it.

## Falsifiable hypothesis

If direct neutral-executor orchestration produces the same result as the
explicit compatibility bridge, then the orchestration gates are independent of
the legacy runner interface.

## Acceptance criteria

- direct neutral executor reaches existing acceptance flow;
- direct and bridged paths are behaviorally equivalent;
- blocked and failed states remain fail-closed;
- no fallback or executor switch is introduced;
- existing orchestration tests remain passing.
