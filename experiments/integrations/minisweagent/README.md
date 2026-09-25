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

## One-command local qualification

On a machine with Git, Python 3.12+ and a running Docker daemon:

```bash
python tools/run_mini_v246_provider_free.py
```

The runner performs the complete provider-free block in order:

1. verifies Git and Docker availability;
2. runs the focused CodePro reference-contract tests;
3. fetches the exact upstream mini-SWE-agent commit;
4. verifies the exact bundled config Git blob;
5. creates an isolated temporary Python environment;
6. installs the pinned upstream mini-SWE-agent;
7. runs the Docker/Linux preflight;
8. runs one provider-free SWE-bench task environment probe;
9. writes evidence under
   `logs/architecture/mini-v246-provider-free-local/`.

No provider/model is called.

The final `runner-summary.json` is the authoritative local classification for
this orchestration attempt. A non-zero exit is a blocked/failed gate, not a
benchmark failure.

## Provider-free preflight only

For manual inspection of an already-pinned mini checkout:

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

## Provider-free task environment only

After preflight:

```bash
python experiments/integrations/minisweagent/provider_free_task_harness.py \
  --mini-repo /path/to/mini-swe-agent \
  --subset verified \
  --split test \
  --instance sympy__sympy-14711 \
  --repeat 1 \
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
