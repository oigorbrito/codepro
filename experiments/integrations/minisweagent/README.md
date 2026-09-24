# mini-SWE-agent benchmark reference integration

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

## Provider-free preflight

Run from the CodePro repository with a local checkout of the pinned mini repo:

```powershell
python experiments/integrations/minisweagent/preflight.py `
  --mini-repo D:\path\to\mini-swe-agent `
  --output logs\architecture\mini-docker-preflight.json
```

This checks, without calling a model/provider:

1. exact mini commit;
2. exact bundled SWE-bench config Git blob;
3. Docker CLI;
4. Docker daemon access.

If an already-available Linux image can be used for a container execution probe:

```powershell
python experiments/integrations/minisweagent/preflight.py `
  --mini-repo D:\path\to\mini-swe-agent `
  --probe-image python:3.11-slim `
  --output logs\architecture\mini-docker-preflight.json
```

The tool deliberately has no local/Git-Bash/SWE-ReX/Modal fallback.

## Reference run

After provider-free preflight passes, use the upstream runner rather than a
CodePro reimplementation:

```text
mini-extra swebench
  --subset <frozen subset>
  --split <frozen split>
  --filter <frozen task id>
  --workers 1
  --output <new qualification-v2 output>
```

The bundled upstream `swebench.yaml` is the default. If a different
model/provider is the intended experimental treatment, layer only those fields
in a second config and freeze the resulting treatment identity. Do not copy and
edit the reference file.

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

## Verification

A generated patch/trajectory is not a successful benchmark result. Resolution
claims require the frozen official SWE-bench evaluation path/verifier.

See:

- `docs/decisions/0142-benchmark-faithful-mini-swebench-substrate.md`
- `docs/benchmark-fidelity-audit.md`
