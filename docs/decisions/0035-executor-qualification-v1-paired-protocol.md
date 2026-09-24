# 0035 — Executor Qualification v1: paired protocol

## Status

Contract implemented. Real qualification is `NOT_EXECUTED` until two concrete
executors produce observations under this protocol.

## Decision

The first executor comparison is a paired, executor-only experiment. Routing,
fallback, retry policy changes, composition and multi-agent behavior are out of
scope. Every executor receives the same task/revision/acceptance definition,
model, environment, budget, treatment, verifier identity and instrumentation
identity.

The harness validates comparability before analysis. It does not rank, select,
accept or promote an executor.

## Falsifiable hypothesis

Two independently implemented executors can pass through the same Codepro
execution, verification and evidence pipeline without executor-specific
branches, while preserving comparable observations for every task/replicate
cell.

## Acceptance criteria

- at least two distinct executor identities are present;
- every `(task, revision, acceptance definition, replicate)` cell has one trial
  for each executor;
- no control dimension differs inside a paired cell;
- verifier and instrumentation identities are present and equal by experiment;
- raw evidence and terminal outcomes exist for every trial;
- `BLOCKED`, `UNKNOWN`, incomplete cells and control mismatches are retained as
  non-passing states;
- the report contains resolution, patch validity, cost, wall time, tokens,
  invocations, retries, failures and blocked rates where observed;
- no routing or fallback is invoked.

Passing these criteria makes the observations comparable. It does not prove
that an executor is better, generally reliable, or ready for promotion.

## Required run record

The experiment must freeze:

1. task-set manifest and repository revisions;
2. executor identities and configuration digests;
3. model/provider identities, if applicable;
4. environment and sandbox identity;
5. budget and invocation limits;
6. treatment identity;
7. verifier and instrumentation identities;
8. serial execution order and replicate identifiers;
9. raw execution, verification and acceptance evidence;
10. independent acceptance decision.

## Explicit non-goals

This decision does not authorize a real provider, executor, external CLI,
benchmark publication, routing treatment or release promotion. Those require a
later decision backed by executed evidence.
