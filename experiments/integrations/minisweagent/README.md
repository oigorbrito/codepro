# mini-SWE-agent v2.4.6 reference integration

This directory preserves the execution substrate encoded by the pinned
mini-SWE-agent SWE-bench profile. It does not reimplement mini-SWE-agent inside
CodePro.

## Frozen reference

```text
repository = SWE-agent/mini-swe-agent
version = v2.4.6
commit = a83fcae82d2a08f0ee0c688f9d137b3566c097f8
config blob = 106decd160e72e5164e29d15d23da354c29c309d
```

The mirrored `swebench-v2.4.6-reference.yaml` is an exact upstream reference.
Do not edit it. Any future model/provider change must be a declared treatment
delta.

## Provider-free preflight

```bash
python experiments/integrations/minisweagent/preflight.py \
  --mini-repo /path/to/mini-swe-agent \
  --output logs/architecture/mini-v246-preflight.json
```

Optional Linux container probe:

```bash
python experiments/integrations/minisweagent/preflight.py \
  --mini-repo /path/to/mini-swe-agent \
  --probe-image python:3.11-slim \
  --output logs/architecture/mini-v246-preflight.json
```

Checks:

1. exact upstream commit;
2. clean upstream worktree;
3. exact bundled config Git blob;
4. Docker CLI;
5. Docker daemon;
6. optional Linux container execution.

No provider/model is called.

## Provider-free task environment

After preflight:

```bash
python experiments/integrations/minisweagent/provider_free_task_harness.py \
  --mini-repo /path/to/mini-swe-agent \
  --subset verified \
  --split test \
  --instance sympy__sympy-14711 \
  --repeat 3 \
  --output logs/architecture/mini-v246-task-env.json
```

The harness imports upstream:

- `DATASET_MAPPING`;
- `get_swebench_docker_image_name`;
- `get_sb_environment`;
- bundled config loading.

No model is created.

## Classification

```text
BENCHMARK_SUBSTRATE_READY
REFERENCE_PROVIDER_FREE_TASK_ENV_READY
BLOCKED_REFERENCE_IDENTITY
BLOCKED_MINI_SWEBENCH_ENVIRONMENT
TASK_IMAGE_PROVENANCE_MISMATCH_CONFIRMED
```

None of these states is a benchmark result or executor promotion.

## References

- `docs/decisions/0142-benchmark-faithful-mini-swebench-substrate.md`
- `docs/decisions/0143-swebench-prepared-repo-state.md`
- `docs/audits/mini-v246-qualification-readiness-20260925.md`
