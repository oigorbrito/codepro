# ADR 0143 — Validate SWE-bench prepared repository state, not HEAD equality

## Status

Accepted for the Qualification v2 experimental lineage. Not promoted.

## Context

Qualification v2 initially treated this condition as a required task-image invariant:

```text
HEAD == instance.base_commit
```

That assumption produced `OFFICIAL_TASK_IMAGE_BASE_COMMIT_MISMATCH` for
`sympy__sympy-14711`, even though:

- the image was the current registry image returned by the pinned mini runner;
- direct Docker execution succeeded;
- the Linux control plane was stable;
- the upstream mini `DockerEnvironment` started, executed, and cleaned the task image;
- the official SWE-bench negative verifier control passed.

SWE-bench task images are prepared execution environments. The benchmark
contract is not adequately represented by raw equality between the prepared
image HEAD and the task's `base_commit`. Preparation may legitimately create
committed state after the base revision.

The previous equality requirement was therefore an unverified local invariant,
not a property inherited from the benchmark.

## Decision

For provider-free SWE-bench task-environment qualification, CodePro validates
repository state using these rules:

1. the task `base_commit` must be an ancestor of the prepared `HEAD`;
2. the initial working tree must be clean;
3. commits between `base_commit` and prepared `HEAD` are captured as evidence;
4. `HEAD == base_commit` is recorded as an observation, not required as a pass condition;
5. image identity, dataset identity, task identity, and prepared repository state
   are recorded separately;
6. the environment is instantiated through the pinned upstream mini runner,
   not by a CodePro reimplementation;
7. no model/provider is created during provider-free qualification.

A non-ancestor base commit is a material provenance failure:

```text
BASE_COMMIT_NOT_ANCESTOR
→ TASK_IMAGE_PROVENANCE_MISMATCH_CONFIRMED
```

A dirty initial working tree is also rejected.

## Harness implementation

The experimental harness is:

```text
experiments/integrations/minisweagent/provider_free_task_harness.py
```

It imports directly from the pinned mini-SWE-agent checkout:

- `DATASET_MAPPING`;
- `get_swebench_docker_image_name`;
- `get_sb_environment`;
- bundled config loading.

It deliberately does not copy those semantics into CodePro.

## Reproducibility requirements

Every qualification record should preserve, when available:

- CodePro commit;
- mini-SWE-agent commit;
- bundled config Git blob;
- dataset repository/subset/split;
- dataset revision or fingerprint;
- instance ID;
- instance `base_commit`;
- image name;
- image digest/image ID when resolved;
- prepared HEAD;
- ancestry result;
- commits ahead of base;
- initial working-tree status;
- environment class;
- Docker identity;
- verifier identity;
- unique verifier run ID;
- provider-called flag.

Mutable tags such as `:latest` are insufficient as the only image identity.
Resolved digest/ID must be captured as evidence even when the pinned upstream
runner itself uses a mutable tag.

## Verifier discipline

SWE-bench evaluation is authoritative for resolution claims. CodePro patch
checks remain local evidence only.

Verifier runs must use unique `run_id` values for distinct predictions or
controls. The SWE-bench harness may cache by `run_id` and instance, so reusing
a run ID for a changed patch can produce misleading cached evidence.

Negative and positive controls should be kept separate from agent runs and
labelled as controls.

## Backend discipline

The restored reference baseline remains the pinned mini Docker path.

SWE-ReX Docker/Modal, Harbor, routing, recovery, compaction, handoff, and other
CodePro mechanisms are valid future treatment candidates, not silent baseline
substitutions.

A supported backend is not evidence that it produced the reference result.

## Empirical interpretation

A local mechanism pass demonstrates only that the tested mechanism behaved as
specified in the recorded environment. It does not establish benchmark
performance.

Performance claims require a frozen workload and paired or otherwise controlled
comparison with the official verifier outcome, plus token/cost/wall-time and
failure measurements where relevant.

## Qualification lineage

Qualification Run v1 remains unchanged:

- `Gate A = PASS`;
- `Gate B = BLOCKED`;
- `verifier = NOT_EXECUTED`;
- `promotion = NOT_AUTHORIZED`.

Qualification v2 remains `REFERENCE_BASELINE_PARTIALLY_FAITHFUL` until the
provider-free upstream task path and subsequent provider/model path are
demonstrated.

## Removal condition

Replace this rule only if the pinned benchmark/harness reference establishes a
stronger task-state invariant. Any replacement must cite the exact upstream
version and include a regression test for the previous false-positive case.
