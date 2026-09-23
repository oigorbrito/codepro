# ADR 0084: Enforce invocation budget at the orchestration seam

## Status

Accepted for local architectural evidence; partial enforcement only.

## Decision

When an execution plan contains a budget, orchestration consumes one immutable
ledger entry before invoking any runner and records the resulting ledger in the
execution event data. A budget that rejects the invocation blocks before the
runner is called. The plan reference is the deterministic local consumption
identity for this single pipeline invocation.

This decision enforces attempts/invocations at the neutral seam. Token, wall
time and cost consumption still require adapter-reported measurements and are
not inferred from this ledger entry.

## Falsifiable hypothesis and acceptance criteria

H1: a zero invocation budget never reaches a runner. The focused test must
prove that the runner is not called and that the result is explicitly blocked.

## Evidence

The complete local suite is the acceptance evidence for this block. External
provider/model/Docker/SWE-bench qualification remains unchanged.
