# SWE-bench Science benchmark audit — Phase 1

Date: 2026-09-25
Issue: #35 — Benchmark Expansion v1
Status: PHASE_1_COMPLETE
Execution status: NOT_EXECUTED
Adoption status: NOT_DECIDED

## Decision basis

```text
problem_class = benchmark qualification / evaluation methodology
decision = complete documentary audit before any smoke or benchmark run
basis_type = OFFICIAL_DOC + UPSTREAM_IMPL + PAPER
basis_ref =
  - https://github.com/OpenMOSS/SWE-bench-Science
  - https://arxiv.org/abs/2608.19799
  - https://swescience.github.io/
supported_claim =
  benchmark composition, runtime architecture, licensing boundary,
  verifier separation, public leaderboard structure, and published failure modes
applicability =
  determine whether SWE-bench Science adds evaluation signal useful to CodePro
  without placing a new benchmark on the operational-release critical path
deviation = none
```

## 1. Composition

The current public release documents:

- 119 tasks;
- 98 GitHub repositories;
- 20 scientific domains;
- three task paradigms:
  - issue-driven;
  - expert-exploratory;
  - engineering-integration;
- 96 tasks in the default unrestricted selection;
- 23 tasks behind an explicit restricted-license gate;
- 91 tasks in the science-knowledge ablation selection.

The benchmark targets repository-level scientific software engineering rather
than isolated function synthesis. The paper identifies recurring failure modes
in scientific knowledge/abstraction, exploration, repair coverage/integration,
and generalization.

Assessment:

```text
SIGNAL_OVERLAP_WITH_CODEPRO = PARTIAL
DISTINCT_SIGNAL = YES
```

The benchmark exercises semantic and integration constraints that are not
directly represented by CodePro's provider-free product suite.

## 2. Runtime and verifier architecture

The benchmark release separates:

```text
task selection
  ->
environment image
  ->
runtime-selected harness
  ->
model.patch
  ->
separate verifier image
  ->
clean rebuild / programmatic verification
```

Current upstream documentation states:

- one environment image per task;
- one verifier image per task;
- immutable Docker Hub image references;
- target platform `linux/amd64`;
- Pier as the evaluation runner, currently documented with
  `datacurve-pier==0.3.0`;
- Python 3.12+;
- Docker Desktop or Docker Engine with amd64 support;
- Apple Silicon support through amd64 emulation;
- harness selection at runtime, including Codex, Claude Code,
  mini-swe-agent, and other Pier-compatible harnesses.

The public benchmark release intentionally excludes reference-answer patches,
private verifier tests, credentials, and historical agent trajectories.

Assessment:

```text
REPRODUCIBLE_RUNTIME_MODEL = YES
VERIFIER_SEPARATION = YES
HARNESS_COUPLING = LOW_TO_MODERATE
CODEPRO_CONCEPTUAL_COMPATIBILITY = HIGH
```

The architecture matches CodePro's desired separation of executor output from
verification better than a benchmark in which the agent and grader share one
mutable environment.

## 3. Licensing boundary

The repository tooling/release metadata are MIT-licensed, but task materials
retain their upstream licenses.

Upstream currently documents:

```text
default selection = 96 tasks
restricted selection = 23 tasks
GPL/LGPL/AGPL-family = 18 tasks
other restricted-material tasks = 5 tasks
```

Restricted task IDs:

```text
003 019 020 021 023 026 032 035 057 066 074 075
082 083 084 085 096 097 098 100 101 102 118
```

The `--allow-restricted-licenses` flag changes selection only. It does not
waive or replace upstream license obligations.

### Hard70 interaction

The published Hard70 task list includes multiple restricted IDs. Therefore:

```text
HARD70 != LICENSE-NEUTRAL DEFAULT
```

CodePro must not adopt Hard70 blindly as its default subset. Any Hard70 use
must either:

1. explicitly authorize the applicable restricted licenses/materials; or
2. derive and freeze a CodePro-specific unrestricted subset and label it as
   such rather than calling it the canonical Hard70.

For a low-friction first integration, the upstream default-96 selection is the
cleanest legal/operational starting boundary.

## 4. Reproducibility and evidence capture

Upstream records:

- selected task IDs;
- selection hash;
- image references;
- platform;
- Pier version;
- agent/model settings;
- redacted invocation;
- per-task verifier reward;
- CTRF output;
- verifier stdout;
- aggregate JSON/CSV summaries.

This maps well to CodePro evidence concepts:

```text
selection hash / task IDs
  ~ workload identity

image digests / platform / runner version
  ~ environment identity

agent / model / harness settings
  ~ treatment identity

model.patch / trajectory
  ~ raw execution evidence

reward / verifier output
  ~ verification evidence
```

Upstream benchmark evidence must remain external evidence:

```text
UPSTREAM_BENCHMARK_RESULT != CODEPRO_LOCAL_ACCEPTANCE
```

## 5. Hardware and runtime requirements

The official public documentation establishes the following minimum operational
requirements:

- Python 3.12+;
- Docker with `linux/amd64` support;
- local storage/network sufficient to obtain per-task environment and verifier
  images;
- runner/provider credentials for real agent runs.

The upstream documentation reviewed for this audit does not publish one fixed
CPU/RAM/storage requirement or one authoritative per-task monetary cost for
the full benchmark. CodePro therefore must not invent those values.

Assessment:

```text
FIXED_HARDWARE_REQUIREMENT = NOT_PUBLISHED_AS_SINGLE_GLOBAL_VALUE
FIXED_FULL_RUN_COST = NOT_PUBLISHED
COST_DRIVER =
  task image transfer/storage
  + verifier/runtime duration
  + selected model/provider usage
  + concurrency
```

A future smoke phase should measure these locally rather than extrapolate from
leaderboard token counts.

## 6. Leaderboard and cost instrumentation

The public leaderboard reports pass@1 together with model/harness
configuration and mean token consumption per task. It also exposes a Hard70
view.

This makes the benchmark useful for:

- correctness/cost trade-off analysis;
- harness/model interaction analysis;
- task difficulty analysis.

But leaderboard data is not a controlled CodePro comparison because model,
harness, provider settings, and run dates differ.

```text
PUBLIC_LEADERBOARD = EXTERNAL_SIGNAL
PUBLIC_LEADERBOARD != CODEPRO_TREATMENT_COMPARISON
```

## 7. Contamination and public/private boundary

The public benchmark intentionally keeps verifier tests and reference-answer
material out of the agent-visible release. This reduces direct leakage from the
runtime bundle.

However, the tasks, repositories, paper, benchmark metadata, and leaderboard
are public. Therefore public benchmark familiarity and model-training exposure
remain possible contamination risks.

CodePro should treat SWE-bench Science as:

```text
PUBLIC_DIAGNOSTIC_BENCHMARK
!=
PRIVATE_UNSEEN_HOLDOUT
```

It is suitable for comparative diagnostics and failure analysis, not as the
sole independent acceptance authority for CodePro.

## 8. Incremental value to CodePro

Distinct signal identified in Phase 1:

- numerical/scientific invariants;
- repository-level integration across heterogeneous scientific projects;
- clean verifier rebuild after patch generation;
- explicit separation of environment and verifier images;
- failure categories involving domain knowledge and incomplete integration;
- token/cost visibility on the public leaderboard.

Overlap with existing CodePro evidence:

- immutable task/environment identity;
- explicit harness/model configuration;
- raw result preservation;
- separate verification;
- fail-closed interpretation of missing/infrastructure evidence.

Assessment:

```text
ADDITIONAL_SIGNAL = YES
RELEASE_CRITICAL = NO
CORE_RUNTIME_DEPENDENCY = NO
BENCHMARK_REPLACEMENT = NO
```

## 9. Phase-1 conclusion

Phase 1 finds no documentary reason to reject SWE-bench Science as a future
CodePro evaluation family.

It should remain a complementary evaluation surface rather than enter the
operational-release critical path.

The cleanest future execution boundary, if explicitly authorized, is:

```text
candidate = default unrestricted selection
first execution = tiny infrastructure/provider smoke
harness = one already-qualified CodePro-compatible executor
purpose = reproduce setup/evidence/verifier behavior
quality claim = none
```

Hard70 should not be the first default because its canonical list crosses the
restricted-license boundary.

## 10. Gate state

```text
PHASE_1_BENCHMARK_AUDIT = COMPLETE
PHASE_2_SMOKE_REPRODUCTION = NOT_EXECUTED
BENCHMARK_ADOPTION = NOT_DECIDED
PROMOTION = NOT_AUTHORIZED
```

No benchmark task was executed for this audit. No leaderboard result is
reclassified as CodePro evidence.

## Primary external references

- SWE-bench Science repository:
  https://github.com/OpenMOSS/SWE-bench-Science
- Paper:
  https://arxiv.org/abs/2608.19799
- Leaderboard:
  https://swescience.github.io/
- Dataset/release contract:
  https://github.com/OpenMOSS/SWE-bench-Science/blob/main/docs/dataset-contract.md
- Architecture:
  https://github.com/OpenMOSS/SWE-bench-Science/blob/main/docs/architecture.md
