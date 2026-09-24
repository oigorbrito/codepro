# ADR 0025 — Qualification before executor binding

## Status

Accepted for empirical validation.

## Context

CodePro can now observe commands and detect whether known executor binaries are present, but availability is not evidence that an executor is suitable for a required capability.

Benchmark harnesses generally make model/environment identities explicit rather than allowing the evaluator to silently choose them. SWE-bench predictions carry a model identity, while SWE-agent and mini-SWE-agent use explicit model/environment configuration. These patterns support keeping runtime identity and capability qualification explicit rather than implicit.

References reviewed:

- SWE-bench evaluation format:
  https://github.com/SWE-bench/SWE-bench/blob/main/docs/assets/evaluation.md
- SWE-agent configuration:
  https://github.com/SWE-agent/SWE-agent/blob/main/docs/config/config.md
- mini-SWE-agent YAML configuration:
  https://github.com/SWE-agent/mini-swe-agent/blob/main/docs/advanced/yaml_configuration.md

These references inform falsifiable properties; they are not CodePro dependencies.

## Decision

Introduce a pure qualification/binding boundary:

- `CapabilityRequirement`
  - requirement identity;
  - capability identity;
  - source reference.

- `ExecutorRuntime`
  - executor identity/version;
  - adapter identity/version;
  - availability observation;
  - availability evidence reference.

- `ExecutorQualification`
  - exact executor + adapter identity;
  - capability identity;
  - `QUALIFIED` or `NOT_QUALIFIED`;
  - non-empty evidence references.

- `ExecutorBinding`
  - `BOUND`;
  - `REQUIRE_QUALIFICATION`;
  - `BLOCKED`;
  - explicit reason code.

## Binding rules

1. Availability alone never produces a binding.
2. Qualification is exact to executor version and adapter version.
3. Qualification for one capability cannot satisfy another capability.
4. Exactly one available + qualified identity may bind.
5. Zero available executors blocks.
6. Available but unqualified identities require qualification.
7. Qualified but unavailable executors block.
8. Multiple available + qualified identities block as ambiguous.
9. No score, rank, priority, or fallback is inferred.
10. Routing remains independent from executor identity.

## Normative invariants

```text
AVAILABLE != QUALIFIED
QUALIFIED != SELECTED_BY_RANK
ROUTE != EXECUTOR_NAME
VERSION_CHANGE != SAME_QUALIFICATION
ADAPTER_CHANGE != SAME_QUALIFICATION
AMBIGUOUS != AUTO_SELECT
```

## Empirical acceptance

Tests must demonstrate:

- single exact qualified binding;
- availability without qualification;
- executor-version mismatch;
- adapter-version mismatch;
- explicit not-qualified state;
- qualified but unavailable state;
- no available executor;
- capability mismatch;
- multiple qualified executors block instead of rank;
- candidate-order invariance;
- duplicate identity rejection;
- evidence canonicalization;
- deterministic binding serialization;
- architecture guard against routing/project coupling;
- mutation probe that detects removal of ambiguity blocking;
- existing command, chassis, fingerprint, and cross-Python checks remain green.

## Non-goals

- concrete Codex/Claude/Gemini adapters;
- executor scoring or benchmarking inside the runtime;
- routing by executor name;
- automatic fallback;
- provider/model selection;
- task execution orchestration;
- recovery;
- acceptance;
- promotion.

## Removal condition

Remove or replace this boundary if a simpler mechanism preserves exact qualification identity, evidence binding, ambiguity blocking, and executor independence.
