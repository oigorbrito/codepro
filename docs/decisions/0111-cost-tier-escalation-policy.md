# 0111 — Cost-tier escalation policy

## Status

Accepted as an experimental policy. Not implemented as automatic routing and
not eligible for promotion until executor qualification and non-routed tier
measurements exist.

## Decision

Codepro will model cost as an economic treatment variable, not as a proxy for
quality, intelligence, or preference. Candidate options are classified into
cost tiers:

- `FREE_SHORT` — free option hypothesized to be suitable for short/local tasks;
- `FREE_GENERAL` — second free option hypothesized to cover broader tasks;
- `FREE_LARGE_CONTEXT` — free option with more context/state capacity;
- `SUBSCRIPTION` — already-paid subscription capacity;
- `PAYG` — usage-priced API, last economic tier.

The tier label does not assert task suitability. Suitability is measured from
the paired observations.

## Experimental sequence

1. enable a second independent executor;
2. qualify executors under decision 0035;
3. run the same frozen task sample across all eligible candidates without
   routing or cascade escalation;
4. measure the economic/functional matrix;
5. define the fixed lowest-cost eligible policy as `Economic Baseline v1`;
6. test explicit escalation against that baseline;
7. only then test task/context-based routing;
8. compare every treatment against the fixed baseline and report cost-quality
   trade-offs.

No candidate is silently retried on another tier during steps 3–5.

## Falsifiable hypotheses

- H1: at least one lower-cost tier resolves a non-trivial subset of the frozen
  task set under the shared verifier;
- H2: a simple explicit escalation rule can improve verified resolution per
  unit cost over the lowest-cost baseline without exceeding declared latency
  and retry budgets;
- H3: a more complex router must outperform the simple escalation baseline on
  predeclared held-out tasks, not merely consume more compute.

## Required observation matrix

Each candidate/task/replicate cell records:

`task → executor → provider → model → tier → marginal cost → context limit →
resolved → patch validity → latency → tokens/context used → calls → retries →
termination reason → blocked/failure class`.

`executor`, `provider`, `model`, `marginal_cost`, `context_limit`, and
`termination_reason` are separate fields. A provider quota, context limit, or
early termination must not be attributed to executor quality.

The task revision, verifier identity, acceptance definition, environment,
budget, instrumentation, serial order, and replicate must be frozen and
identical within a comparison block. Missing cost or context usage remains
`UNKNOWN`; it is never inferred as zero.

## Promotion criteria

Economic Baseline v1 requires complete comparable cells and raw evidence for
the declared sample. Escalation requires a predeclared signal of insufficiency
and must preserve the original attempt and its evidence. Routing promotion
requires a held-out comparison against the economic baseline with improved
verified resolution per unit cost and no unacceptable regression in latency,
blocked rate, patch validity, or reproducibility.

Until those criteria are met, this decision is a protocol and hypothesis, not
evidence that any tier or routing policy is effective.
