# ADR 0097: Restored attempt audits expose the safe resume decision

## Status

Accepted for local architectural evidence.

## Decision

`RestoredChainAudit` includes the `ResumeDecision` derived from its replayed
chain and terminal state. Loading an attempt therefore exposes both evidence
integrity and the safe continuation boundary. The audit does not execute the
decision or mutate artifacts.

## Falsifiable hypothesis and acceptance criteria

H1: an audited attempt cannot be consumed for resume without an explicit
decision. The restored-chain test must expose `RESTART_REQUIRED` when execution
evidence is absent.

## Consequences

Resume services can consume one audited result instead of reimplementing replay
logic. They must still create a new attempt for restart/replan actions.
