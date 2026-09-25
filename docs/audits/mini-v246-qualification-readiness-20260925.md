# mini-SWE-agent v2.4.6 qualification readiness — Phase 0

Date: 2026-09-25
Issue: #36 — Mini v2.4.6 Qualification
Status: PHASE_0_COMPLETE
Runtime qualification: NOT_EXECUTED
Executor promotion: NOT_AUTHORIZED

## Decision basis

```text
problem_class = executor reference adoption / qualification precondition
decision = freeze upstream v2.4.6 semantics before any CodePro runtime work
basis_type = OFFICIAL_DOC + UPSTREAM_IMPL + PROJECT_EVIDENCE
basis_ref =
  - SWE-agent/mini-swe-agent tag v2.4.6
  - commit a83fcae82d2a08f0ee0c688f9d137b3566c097f8
  - upstream SWE-bench configuration and runner at that commit
  - CodePro PR38 experimental implementation, used as prior evidence only
supported_claim =
  exact execution substrate and which integration properties can be adopted
  directly without inventing CodePro agent semantics
applicability =
  Issue #36 asks whether v2.4.6 can satisfy CodePro compatibility/runtime
  contracts before more v1-specific optimization
deviation =
  no runtime is promoted or claimed ready by this Phase 0 document
```

## 1. Repository-state correction

Issue #36 currently cites:

- `docs/version-freshness-policy.md`;
- `docs/audits/dependency-executor-freshness-20260924.md`.

Those files are not present on current `main`.

The mini-SWE-agent v2.4.6 experimental integration is also not present on
current `main`; it remains on draft PR38.

Therefore:

```text
ISSUE_36_REFERENCE_INTENT = VALID
ISSUE_36_CURRENT_MAIN_SUBSTRATE = ABSENT
PR38 = PRIOR_EXPERIMENTAL_EVIDENCE
PR38 != CURRENT_PRODUCT_STATE
```

Do not run Phase 1 as though the PR38 harness were already part of the product.

## 2. Exact upstream reference

The upstream tag resolves to:

```text
repository = SWE-agent/mini-swe-agent
version = v2.4.6
commit = a83fcae82d2a08f0ee0c688f9d137b3566c097f8
```

The bundled SWE-bench configuration at that revision specifies:

```text
environment_class = docker
cwd = /testbed
interpreter = ["bash", "-c"]
BASH_ENV = /root/.bashrc
per-command timeout = 60 seconds
step_limit = 250
cost_limit = 3
```

The upstream single-instance runner:

1. loads the SWE-bench dataset/instance;
2. resolves the default bundled SWE-bench config;
3. constructs the environment through upstream `get_sb_environment`;
4. constructs the selected model/agent through upstream factories;
5. runs the agent on the instance problem statement.

No CodePro-specific planner, router, tool selector, fallback, or recovery loop is
required to reproduce this execution shape.

## 3. What can be adopted directly

The following are **reference semantics**, not hypotheses requiring a CodePro
A/B experiment before implementation:

### 3.1 Identity

Pin the exact upstream release/commit and configuration identity.

```text
MINI_REFERENCE_VERSION = v2.4.6
MINI_REFERENCE_COMMIT = a83fcae82d2a08f0ee0c688f9d137b3566c097f8
```

### 3.2 Environment substrate

For the SWE-bench reference profile:

```text
Docker/Linux
/testbed
bash -c
BASH_ENV=/root/.bashrc
```

Host-local Git Bash/MSYS2 is not reference-equivalent.

### 3.3 Runner ownership

Use upstream mini-SWE-agent environment/config/runner behavior rather than
reimplementing the agent loop inside `arkx`.

CodePro may wrap it with:

- identity/provenance;
- authority and scope;
- budget;
- invocation;
- raw trajectory/patch capture;
- verification references;
- event log/replay;
- acceptance/promotion state.

### 3.4 Fail-closed backend

If the frozen reference profile requires Docker and Docker is unavailable:

```text
DOCKER_UNAVAILABLE -> BLOCKED
```

Do not silently switch to LocalEnvironment, Git Bash, SWE-ReX, Modal, or another
backend and call it the same treatment.

### 3.5 Configuration layering

The upstream config loader supports layered configuration. Model/provider
treatment changes should therefore be layered over the frozen reference rather
than editing the reference config in place.

```text
REFERENCE_CONFIG + DECLARED_TREATMENT_DELTA
!=
MUTATED_REFERENCE_CONFIG
```

## 4. What still requires runtime qualification

The following cannot be established by documentation alone:

- Docker CLI/daemon availability in the selected execution environment;
- successful container start and cleanup;
- task-image acquisition;
- prepared repository state for a real SWE-bench instance;
- whether `environment.execute` completes reliably under the local/runtime
  infrastructure;
- timeout behavior observed in that environment;
- trajectory persistence;
- patch extraction/capture;
- provider/model invocation;
- official verifier execution;
- end-to-end compatibility with CodePro event/evidence contracts.

These remain:

```text
NOT_EXECUTED
```

and must not be inferred from upstream benchmark performance.

## 5. PR38 decomposition

PR38 contains useful work, but it is a 28-commit, 19-file draft based on an old
`main`. It must not be merged wholesale.

The reusable concepts are:

- ADR 0142's Docker/Linux substrate correction;
- exact upstream v2.4.6 pin;
- exact upstream SWE-bench config mirror;
- provider-free identity/Docker preflight;
- provider-free task-environment probe;
- no-fallback rule.

The parts that require reconciliation before reuse are:

- nested `AGENTS.md` files, because root agent policy changed after PR38;
- project-contract edits, because current `main` architecture/state advanced;
- copied reference config, because source identity should preferably be verified
  against upstream rather than treated as independently editable product code;
- tests/harness assumptions tied to the historical PR38 branch;
- historical audit documents that may describe states no longer current.

Therefore:

```text
PR38_WHOLESALE_MERGE = NO
PR38_SELECTIVE_EXTRACTION = ALLOWED
```

## 6. Minimal Phase-1 implementation block

When runtime qualification is authorized, implement **one block**, not a chain
of corrective PRs:

```text
A. reference identity
   exact tag + commit + config identity

B. provider-free preflight
   Docker CLI + daemon + Linux container probe

C. upstream task environment probe
   use upstream get_sb_environment
   verify /testbed + Linux + prepared repo provenance
   verify cleanup

D. evidence artifact
   exact commands
   stdout/stderr
   exit/timeout
   image identity
   task/revision
   upstream commit/config
```

Only if A-D complete may a provider/model call be considered.

That block is infrastructure/compatibility qualification only.

```text
PHASE_1_PASS != MODEL_QUALITY
PHASE_1_PASS != BENCHMARK_PASS
PHASE_1_PASS != EXECUTOR_PROMOTION
```

## 7. External reference fit

Current upstream documentation confirms that mini-SWE-agent configuration is
split into agent/environment/model/run sections and supports an explicit Docker
environment. The current upstream SWE-bench configuration continues to encode
Docker, `/testbed`, `bash -c`, and `BASH_ENV=/root/.bashrc`.

References:

- https://github.com/SWE-agent/mini-swe-agent/releases/tag/v2.4.6
- https://github.com/SWE-agent/mini-swe-agent/blob/a83fcae82d2a08f0ee0c688f9d137b3566c097f8/src/minisweagent/config/benchmarks/swebench.yaml
- https://github.com/SWE-agent/mini-swe-agent/blob/a83fcae82d2a08f0ee0c688f9d137b3566c097f8/src/minisweagent/run/benchmarks/swebench_single.py
- https://github.com/SWE-agent/mini-swe-agent/blob/main/docs/advanced/yaml_configuration.md
- https://github.com/SWE-agent/mini-swe-agent/blob/main/src/minisweagent/environments/docker.py

## 8. Gate state

```text
PHASE_0_REFERENCE_FREEZE = COMPLETE
DIRECT_ADOPTION_BOUNDARY = DEFINED
PHASE_1_PROVIDER_FREE_RUNTIME = NOT_EXECUTED
PROVIDER_MODEL_RUN = NOT_AUTHORIZED
BENCHMARK_RESULT = NOT_EXECUTED
EXECUTOR_PROMOTION = NOT_AUTHORIZED
```
