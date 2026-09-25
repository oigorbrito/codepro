# mini-SWE-agent benchmark reference integration

## Agent instructions

Repository-wide agent rules live in `AGENTS.md`. This integration has additional benchmark-specific rules in `experiments/integrations/minisweagent/AGENTS.md`. Agents working in this directory must follow both, with the nested instructions taking precedence where more specific.

This directory preserves the execution substrate used by the pinned
mini-SWE-agent SWE-bench configuration instead of reimplementing it inside
CodePro.

## Pinned reference

- repository: `SWE-agent/mini-swe-agent`
- commit: `a83fcae82d2a08f0ee0c688f9d137b3566c097f8`
- version used by the qualification work: `v2.4.6`
- pinned SWE-bench config blob: `106decd160e72e5164e29d15d23da354c29c309d`

`swebench-v2.4.6-reference.yaml` is an exact mirror of the bundled upstream
configuration at that commit. Do not edit it locally. Model/provider changes for
an experiment must be layered as a separate config and frozen as treatment
configuration.

## Engineering rule

The reference baseline must import and exercise upstream behavior rather than
reimplementing it in CodePro.

CodePro qualification code may:

- pin identity;
- record provenance;
- execute controls;
- classify observed outcomes.

It must not silently change:

- environment/backend;
- image derivation;
- task state;
- prompt/tool contract;
- retries/timeouts;
- patch extraction;
- verifier authority.

## Provider-free preflight

Run from the CodePro repository with a local checkout of the pinned mini repo:

```powershell
python experiments/integrations/minisweagent/preflight.py `
  --mini-repo D:\path\to\mini-swe-agent `
  --output logs\architecture\mini-docker-preflight.json
```

This checks, without calling a model/provider:

1. exact mini commit;
2. clean mini worktree;
3. exact bundled SWE-bench config Git blob;
4. Docker CLI;
5. Docker daemon access.

If an already-available Linux image can be used for a container execution probe:

```powershell
python experiments/integrations/minisweagent/preflight.py `
  --mini-repo D:\path\to\mini-swe-agent `
  --probe-image python:3.11-slim `
  --output logs\architecture\mini-docker-preflight.json
```

The tool deliberately has no local/Git-Bash/SWE-ReX/Modal fallback.

## Provider-free task-environment harness

After the infrastructure preflight passes, qualify the real task environment
through the pinned upstream mini runner:

```powershell
python experiments/integrations/minisweagent/provider_free_task_harness.py `
  --mini-repo D:\path\to\mini-swe-agent `
  --subset verified `
  --split test `
  --instance sympy__sympy-14711 `
  --repeat 3 `
  --output logs\architecture\qualification-v2-provider-free-task.json
```

The harness imports these upstream functions directly:

- `DATASET_MAPPING`;
- `get_swebench_docker_image_name`;
- `get_sb_environment`.

It does not instantiate a model.

### Prepared repository-state invariant

Do not require:

```text
prepared HEAD == instance.base_commit
```

The provider-free task harness instead requires:

```text
instance.base_commit is an ancestor of prepared HEAD
AND initial working tree is clean
```

It records:

- prepared HEAD;
- whether HEAD equals base commit;
- ancestry result;
- number of commits ahead;
- prepared commit metadata;
- initial working-tree state.

A non-ancestor base commit is a material provenance failure. A prepared commit
above the base revision is not automatically a failure.

See `docs/decisions/0143-swebench-prepared-repo-state.md`.

## Reference agent run

Only after the provider-free path is ready should a model/provider be introduced.

Use the upstream runner rather than a CodePro implementation:

```text
mini-extra swebench
  --subset <frozen subset>
  --split <frozen split>
  --filter <frozen task id>
  --workers 1
  --output <new qualification output>
```

The bundled upstream `swebench.yaml` is the default. If a different
model/provider is the intended treatment, layer only those fields in a second
config and freeze the resulting treatment identity. Do not copy and edit the
reference file.

## Workload provenance

For every benchmark qualification, record when available:

- dataset repository;
- subset and split;
- dataset revision;
- dataset fingerprint;
- instance ID;
- task `base_commit`;
- task image name;
- resolved image digest/image ID;
- prepared HEAD;
- commits between base and prepared HEAD.

A mutable image tag such as `:latest` is not sufficient as the only provenance
record.

## Verification

A generated patch/trajectory is not a successful benchmark result. Resolution
claims require the frozen official SWE-bench evaluation path/verifier.

Verifier controls and agent runs must use distinct `run_id` values. The
SWE-bench harness may reuse a cached result for the same run ID and instance, so
reusing an identifier for a different prediction can invalidate the evidence.

Recommended control sequence:

1. provider-free task environment;
2. negative verifier control;
3. positive/gold verifier control when available;
4. model/provider qualification;
5. bounded agent run;
6. official verifier outcome.

## Baseline restrictions

The first corrected baseline must not enable CodePro behavior-changing
mechanisms:

- routing;
- executor fallback;
- recovery policy;
- compaction;
- replanning;
- multi-executor handoff;
- treatment-specific task substitution.

CodePro may record provenance and observations only where doing so does not
change agent behavior.

SWE-ReX and Harbor may be evaluated later as explicit treatments or execution
substrates. Their support does not make them equivalent to the pinned Docker
baseline.

## Empirical comparison discipline

After the reference baseline is demonstrated, change one behavior-affecting
variable at a time on the same frozen workload.

Measure at minimum:

- official verifier resolution;
- provider calls;
- tokens;
- cost;
- wall time;
- retries;
- timeouts;
- failure classes.

A smoke test, local pass, supported backend, or synthetic fixture is not a
benchmark result.

## Current references

Historical baseline authority:

- pinned mini-SWE-agent v2.4.6 source/config.

Current corroborating engineering documentation:

- https://www.swebench.com/SWE-bench/reference/harness/
- https://www.swebench.com/SWE-bench/guides/docker_setup/
- https://mini-swe-agent.com/latest/advanced/environments/
- https://mini-swe-agent.com/latest/reference/run/swebench/
- https://www.harborframework.com/docs/agents

See also:

- `docs/decisions/0142-benchmark-faithful-mini-swebench-substrate.md`
- `docs/decisions/0143-swebench-prepared-repo-state.md`
- `docs/benchmark-fidelity-audit.md`
- `docs/benchmark-fidelity-audit-v2-addendum.md`
