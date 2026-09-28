# Phase 4 - Compact model compatibility audit

Date: 2026-09-28

## Frozen runtime

```text
llama.cpp build 11205
commit 95887577ab5fead779581a7030a83c7752ff3234
Windows x64 / CUDA 13.4
NVIDIA GeForce GTX 1650 4 GB
```

## Result

| Candidate | Artifact | CPU | GPU | Context 4096 | Structured output | Unload | Classification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L1 Nanbeige4.2-3B | PASS | PASS | PASS | PASS | PASS | PASS | COMPATIBLE |
| L2 Qwen3.5-4B | PASS | PASS | PASS | PASS | PASS | PASS | COMPATIBLE |
| L3 Granite 4.2 3B | PASS | PASS | PASS | PASS | PASS | PASS | COMPATIBLE |
| L4 SWE-Dev-7B | PASS | PASS | PASS | PASS | PASS | PASS | COMPATIBLE |

## Compatibility observations

| Candidate | CPU gen t/s | GPU gen t/s | VRAM delta MiB | Context 4096 gen t/s |
| --- | ---: | ---: | ---: | ---: |
| L1 | 3.3 | 1.7 | 2698 | 28.1 |
| L2 | 7.2 | 34.7 | 2818 | 36.4 |
| L3 | 9.8 | 47.2 | 2288 | 47.2 |
| L4 | 5.2 | 10.1 | 3534 | 10.6 |

These are compatibility-run observations, not statistical benchmark rankings.

## Caveats

- L1 initial artifact failed load; the verified mainline-compatible artifact passed.
- L1 freeform JSON failed; constrained JSON decoding passed.
- L2-L4 constrained structured output passed.
- Exact same-run GPU offload layer counts remain UNKNOWN.
- L4 stretch execution completed without an OOM signal.

## Gate

```text
ARTIFACT_IDENTITY     = PASS
CPU_LOAD_GENERATION   = PASS
GPU_EXECUTION         = PASS
CONTEXT_4096          = PASS
STRUCTURED_OUTPUT     = PASS
CLEAN_UNLOAD          = PASS
COMPATIBLE            = 4/4
PHASE_4               = COMPLETE
```

```text
COMPATIBLE != SELECTED
SELECTED != PROMOTED
UNKNOWN != ZERO
```

Evidence: `evidence/phase4-model-compatibility/`.

Next execution block: Phase 5 - CodePro local-runtime plumbing.
