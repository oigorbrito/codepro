# P8.2 — Task stratification and evidence confrontation

## Decision

Candidate quality is not a scalar property of a model or harness. P8.2 must
compare a `task stratum × model × harness` cell. The current Wave 0 remains
frozen and is not reclassified retrospectively as mechanism evidence.

The task strata are:

| Stratum | Operational description | Main suspected bottleneck |
| --- | --- | --- |
| T0 | deterministic fixture, one target file, explicit failing test | startup and action compatibility |
| T1 | localized bug, one function or file, reproducible test | local reasoning and editing |
| T2 | several plausible locations or hidden control flow | repository localization and diagnosis |
| T3 | multiple modules, implicit behavior, incomplete test signal | planning and verification |
| T4 | cross-cutting API, dependency, or architectural change | long-horizon coordination |
| T5 | long-horizon, multimodal, multilingual, or non-Python task | generalization and runtime robustness |

Classification is metadata, not a result. A task must not be assigned to a
higher stratum merely because an agent failed on it. Unknown task metadata is
recorded as `UNCLASSIFIED`, never inferred from outcome.

## Task profile

Every future task selection should record, before execution:

```text
repository_scope       = one_file | few_files | multi_module | cross_cutting
localization_ambiguity = explicit | bounded | competing | unknown
behavior_signal        = direct_test | reproducible | implicit | absent
execution_horizon      = fixture | short | iterative | long
language_runtime       = single | multi_language | unknown
```

The stratum is derived from this profile and frozen with the task manifest.
The derivation is not an implementation of C1: it supplies no candidate file,
symbol, or context to an agent.

## Empirical confrontation

The literature supports testing several mechanisms, but does not qualify them
for Arkx:

| Mechanism | External evidence | Evidence class | Arkx interpretation |
| --- | --- | --- | --- |
| minimal scaffold | official SWE-bench leaderboard uses a common mini-SWE-agent/Bash-only setting | official benchmark | control remains necessary |
| workflow without autonomous loop | Agentless reports strong SWE-bench Lite performance at low cost | primary paper, not Arkx | compare against A on T1/T2 |
| repository graph | RepoGraph reports gains when integrated with Agentless and SWE-agent | project/self-reported until independently reproduced | localization hypothesis for T2 |
| AST/repository tools | AutoCodeRover reports Verified results with specialized analysis | project/self-reported | test Python-specific bias on T2/T3 |
| tree search and refinement | SWE-Search reports relative improvement from MCTS/refinement | peer-reviewed paper | search hypothesis for T3/T4 |
| trained verifier | SWE-Gym reports gains from agent/verifier training and best-of-n selection | peer-reviewed paper | verifier hypothesis for T3/T4 |
| distribution shift | SWEE/SWA-Bench reports lower success outside classic SWE-bench distribution | peer-reviewed paper | include T4/T5 before generalizing |

These claims are external evidence only. They do not open B1/C1, establish an
Arkx improvement, or justify comparing scores obtained with different task
strata.

## Candidate allocation

The exploration funnel is deliberately broad:

```text
E0: 20–40 model × harness smoke cells across T0 fixtures
E1: 10–15 cells on T1/T2 deterministic repository fixtures
E2: 6–8 cells on stratified SWE-bench tasks
E3: 2–3 cells on T3/T4/T5 long-horizon or shifted tasks
```

No candidate advances because of a smoke result alone. Advancement requires
the same provider, model identity, generation configuration, executor,
verification authority, and acceptance authority within the comparison cell.

## Current Wave 0 annotation

The two frozen tasks have only provisional metadata descriptions:

```text
sympy__sympy-14711 -> provisional T1
sympy__sympy-24443 -> provisional T2
```

This annotation is not an empirical result and does not change the frozen
Wave 0 protocol. The actual Wave 0 remains `BLOCKED` by provider availability
and timeout evidence.

## Acceptance criteria for future stratified evidence

For a stratum-level claim, Arkx requires:

1. a pre-execution task manifest with frozen profiles;
2. at least one control cell using A;
3. the same authority and executor across compared cells;
4. raw trajectories, usage, environment, and identity artifacts;
5. explicit separation of `BLOCKED`, executor failure, task rejection, and
   accepted resolution;
6. an independent acceptance decision before any promotion.

Unit tests validate only the schema and deterministic derivation. Published
results validate hypotheses and candidate selection, not Arkx effectiveness.

