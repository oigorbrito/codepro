# Benchmark Fidelity Audit v2 — Methodology Addendum

Date: 2026-09-24

This addendum does not rewrite the frozen audit artifact committed at
`ad63b10f88fec9db9237151cad558f5c9645b2c6`. It records a methodological
correction discovered during Qualification v2.

## Correction

The earlier provider-free task-image check assumed:

```text
prepared HEAD == instance.base_commit
```

That equality is not a justified SWE-bench invariant.

The corrected repository-state contract is:

```text
instance.base_commit is an ancestor of prepared HEAD
AND initial working tree is clean
AND any prepared commits are recorded
```

A prepared image can contain committed setup state beyond the task base revision.
The benchmark-relevant question is whether the prepared repository state is
consistent with the task/harness provenance, not whether the final prepared HEAD
is byte-for-byte the task base revision.

## Why this correction matters

The equality assumption produced a false-positive blocking condition after the
following had already passed:

- pinned mini-SWE-agent identity;
- pinned bundled config identity;
- Linux Docker substrate;
- Linux mini control plane;
- generic upstream DockerEnvironment lifecycle;
- real SWE-bench task-image startup/execution/cleanup;
- official verifier negative control.

The correction prevents CodePro from introducing a stronger local rule than the
benchmark itself and then mistaking that rule for upstream evidence.

## Updated provider-free qualification path

```text
pinned mini identity
→ pinned config identity
→ Linux control plane
→ upstream get_swebench_docker_image_name()
→ upstream get_sb_environment()
→ official task image
→ /testbed
→ base_commit ancestry
→ clean prepared working tree
→ capture prepared commits
→ upstream cleanup
→ official verifier controls
```

No model/provider is called in this path.

## Benchmark engineering rules

### 1. Mirror behavior before optimizing it

Reference baselines use the upstream runner/configuration directly whenever
possible. CodePro wrappers may observe but must not silently replace behavior.

### 2. Pin immutable identities

Freeze exact Git commits and config Git blobs. For mutable container tags, record
the resolved image digest/ID as evidence.

For workloads, record dataset repository, subset, split, revision when available,
dataset fingerprint, instance ID, and base commit.

### 3. Separate environment preparation from task identity

`base_commit` identifies the task base revision. The prepared environment may
contain harness-created committed state. Validate ancestry and cleanliness rather
than assuming final HEAD equality.

### 4. Treat the official verifier as authoritative

A patch, trajectory, local test pass, or CodePro P5 check does not establish a
SWE-bench resolve.

Resolution claims come from the frozen official SWE-bench evaluation path.

### 5. Use unique verifier run IDs

The SWE-bench evaluation harness may reuse cached results by `run_id` and
instance. Distinct predictions, gold controls, negative controls, and agent runs
must therefore use distinct run IDs.

### 6. Keep controls explicit

Before an expensive provider run, qualify:

- a negative verifier control;
- a positive/gold control when available;
- environment startup/execution/cleanup;
- task repository provenance.

Do not interpret a smoke test as a benchmark result.

### 7. One manipulated variable at a time

The first CodePro comparison after the reference baseline should change only one
behavior-changing mechanism per treatment:

- provider/model adapter;
- timeout/retry policy;
- compaction;
- routing;
- recovery;
- handoff;
- alternative backend such as SWE-ReX.

Measure official resolution plus tokens, cost, wall time, retries, timeouts and
failure classes.

### 8. Supported backend != benchmark-proven backend

mini-SWE-agent supports Docker, Singularity and SWE-ReX variants. Support alone
does not establish that a backend produced the reference benchmark result.

SWE-ReX and Harbor remain useful comparison/treatment substrates, but are not
silent replacements for the pinned Docker baseline.

## Current external references

- SWE-bench harness reference:
  https://www.swebench.com/SWE-bench/reference/harness/
- SWE-bench Docker setup:
  https://www.swebench.com/SWE-bench/guides/docker_setup/
- mini-SWE-agent environments:
  https://mini-swe-agent.com/latest/advanced/environments/
- mini-SWE-agent SWE-bench runner reference:
  https://mini-swe-agent.com/latest/reference/run/swebench/
- Harbor agent integration reference:
  https://www.harborframework.com/docs/agents

These current references are corroborating engineering guidance. The historical
reference baseline remains pinned to mini-SWE-agent v2.4.6 at
`a83fcae82d2a08f0ee0c688f9d137b3566c097f8`.

## Current classification

The frozen audit conclusion remains:

```text
REFERENCE_BASELINE_PARTIALLY_FAITHFUL
```

The previous task-image equality block should be treated as:

```text
INVALID_LOCAL_INVARIANT
```

until ancestry and prepared-state validation are executed by the corrected
provider-free harness.

Promotion remains:

```text
PROMOTION_NOT_AUTHORIZED
```
