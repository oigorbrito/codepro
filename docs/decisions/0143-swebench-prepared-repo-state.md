# ADR 0143 — Validate SWE-bench prepared repository state, not HEAD equality

## Status

Accepted for provider-free Qualification v2 lineage. Not promoted.

## Context

A prior local invariant assumed:

```text
HEAD == instance.base_commit
```

That is stronger than the benchmark contract. SWE-bench task images are
prepared execution environments and may legitimately contain committed
preparation state after the issue base revision.

Treating HEAD equality as mandatory can therefore create a false provenance
failure.

## Decision

For provider-free task-environment qualification:

1. task `base_commit` MUST be an ancestor of prepared `HEAD`;
2. the initial working tree MUST be clean;
3. commits between `base_commit` and prepared `HEAD` are captured;
4. `HEAD == base_commit` is recorded, not required;
5. image, dataset, task and prepared-repository identities are recorded
   separately;
6. the environment is instantiated through the pinned upstream mini runner;
7. no model/provider is created.

A non-ancestor base commit is a provenance failure:

```text
BASE_COMMIT_NOT_ANCESTOR
-> TASK_IMAGE_PROVENANCE_MISMATCH_CONFIRMED
```

A dirty initial worktree is also rejected.

## Decision basis

```text
problem_class = prepared benchmark repository provenance
decision = ancestry + clean-worktree invariant
basis_type = UPSTREAM_IMPL + LOCAL_EVIDENCE
basis_ref =
  pinned mini-SWE-agent SWE-bench environment construction
  prior false-positive HEAD-equality observation
supported_claim =
  prepared execution state can differ from the raw task base revision while
  preserving ancestry
applicability =
  provider-free qualification of the actual task image
deviation =
  CodePro records stronger provenance detail without changing upstream task state
```

## Reproducibility requirements

Record, when available:

- CodePro commit;
- mini-SWE-agent commit;
- bundled config Git blob;
- dataset/subset/split and revision/fingerprint;
- instance ID and `base_commit`;
- image name and resolved image ID/digest;
- prepared HEAD;
- ancestry result;
- commits ahead of base;
- initial worktree status;
- environment class;
- Docker identity;
- provider-called flag.

Mutable tags are not sufficient as the only image identity.

## Verifier boundary

Provider-free qualification does not establish task resolution.

```text
PROVIDER_FREE_ENV_PASS != BENCHMARK_PASS
```

Official verifier evidence is required for a future resolution claim.
