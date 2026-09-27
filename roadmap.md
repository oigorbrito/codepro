# CodePro Roadmap

This is the canonical living operational roadmap for CodePro.

## Completion discipline

Every implementation or qualification item follows:

```text
IMPLEMENT
-> TEST
-> CAPTURE EVIDENCE
-> VERIFY
-> MARK COMPLETE IN roadmap.md
```

Status markers:

- `[ ]` NOT_STARTED
- `[~]` IN_PROGRESS
- `[x]` COMPLETE
- `[!]` BLOCKED
- `[-]` DEFERRED

A task is not complete merely because code was written.

```text
IMPLEMENTED != COMPLETE
EXECUTED != VERIFIED
VERIFIED != PROMOTED
INFRA_FAILURE != MODEL_FAILURE
```

## Governing strategy

```text
CANDIDATE_POOL_V0 = FROZEN
LOCAL_FIRST = ACTIVE
PAID_API_DEPENDENCY = OFF_CRITICAL_PATH
ROUTER = NOT_YET_IMPLEMENTED
INITIAL_PLATFORM = WINDOWS_NATIVE
WSL2 = DEFERRED_UNTIL_WINDOWS_BASELINE
```

Primary optimization target:

```text
VERIFIED_CAPABILITY / TOTAL_OPERATIONAL_COST
```

Operational cost includes tokens, money, latency, calls, retries, context,
RAM/VRAM, compute, complexity, failure surface, and maintenance burden.

Primary method:

```text
QUALIFY
-> RUN
-> MEASURE
-> REPLICATE
-> ABLATE
-> VALIDATE HELD-OUT
-> PRUNE
-> PROMOTE ONLY WHAT SURVIVES
```

---

## Phase 0 — Strategy / candidate freeze

- [x] Define LOCAL_FIRST strategy.
- [x] Remove paid APIs from the critical path.
- [x] Freeze CANDIDATE_POOL_V0.
- [x] Separate model, scaffold, runtime, sandbox, verifier, and router.
- [x] Establish benchmark-driven / evidence-driven evaluation.
- [x] Defer router implementation until local evidence exists.
- [x] Choose Windows native as the first qualification platform.
- [x] Create canonical living roadmap at `roadmap.md`.
- [x] Add mandatory roadmap-synchronization rule to `AGENTS.md`.
- [x] Restore roadmap and synchronization rule after incidental scaffold cleanup removed them.
- [-] WSL2 qualification.
- [-] Docker GPU qualification.

**Phase status:** COMPLETE

---

## Phase 1 — Windows hardware qualification

### 1.1 Inventory

- [x] GPU: NVIDIA GeForce GTX 1650.
- [x] VRAM: 4096 MiB.
- [x] CPU: Intel Core i5-10300H, 4 cores / 8 threads.
- [x] RAM: 11.87 GB total, 8 GB + 4 GB, 2933 MT/s.
- [x] OS: Windows 11 Home x64.
- [x] WSL2 presence confirmed.
- [x] Docker presence confirmed.

### 1.2 NVIDIA driver baseline

Initial observed driver: `462.30`.

- [x] Update NVIDIA Windows driver to `617.14` WHQL.
  - Local Windows version: `32.0.16.1714`.
- [x] Reboot host.
- [x] Run `nvidia-smi` after reboot.
- [x] Record baseline:
  - NVIDIA-SMI: `617.14`
  - KMD: `617.14`
  - CUDA UMD: `13.4`
  - GPU: `NVIDIA GeForce GTX 1650`
  - VRAM: `4096 MiB`
  - observed idle memory: `182 MiB`
  - WDDM operational
- [x] Confirm GTX 1650 operational after driver update.

**Gate:** `WINDOWS_GPU_BASELINE = PASS`

**Phase status:** COMPLETE

---

## Phase 2 — Local inference runtime qualification

Runtime candidate:

```text
R1 = llama.cpp
PLATFORM = Windows x64
STATUS = CANDIDATE
```

Qualification target selected from upstream release artifacts:

```text
llama.cpp = b11205
upstream_commit = 9588757
backend_target = Windows x64 CUDA 13.4
```

### 2.1 Minimal installation

- [x] Select a reproducible upstream llama.cpp Windows build: `b11205`.
- [x] Record upstream commit: `9588757`.
- [x] Select Windows x64 CUDA 13.4 binary + matching CUDA 13.4 runtime DLL package.
- [x] Install/extract the frozen runtime locally under `D:\\projetos\\codepro-mini-runtime\\downloads\\llama-b11205-bin-win-cuda-13.4-x64`.
- [x] Confirm `llama-cli` executes: `0.5.0-dev`, build `11205`, commit `95887577a`, Windows x86_64.
- [x] Confirm CPU backend with actual model load/generation using `ggml-org/gemma-3-1b-it-GGUF:Q4_K_M`: response `CPU_OK`, prompt throughput `52.2 t/s`, generation throughput `16.5 t/s`.
- [x] Confirm CUDA backend: `--list-devices` detects `CUDA0: NVIDIA GeForce GTX 1650 (4095 MiB, 3296 MiB free)`.
- [x] Record local runtime path and SHA256 checksums:
  - `cudart-llama-bin-win-cuda-13.4-x64.zip` = `738F8C251AC22B70C3AE6F83A10CF222725DF0395246A2CF58F32BDB85FBE668`
  - `llama-b11205-bin-win-cuda-13.4-x64.zip` = `D91178299D1007E162ACAD2776A24D5EF8C834A73F3DB282139ADDC12123BD80`.

### 2.2 CPU smoke test

Previous smoke attempt with `ggml-org/Qwen3.5-0.8B-GGUF:Q4_K_M` failed before model load with `no GGUF files found`; classified as `MODEL_ARTIFACT_RESOLUTION_FAILURE`, not runtime failure. Replacement smoke artifact: `ggml-org/gemma-3-1b-it-GGUF:Q4_K_M`.

- [x] Load a minimal test model: `ggml-org/gemma-3-1b-it-GGUF:Q4_K_M`.
- [x] Generate from a trivial prompt: `CPU_OK`.
- [ ] Record RAM.
- [ ] Record load time.
- [x] Record prompt tokens/s: `52.2 t/s`.
- [x] Record generation tokens/s: `16.5 t/s`.

### 2.3 GPU-offload smoke test

- [~] Run the same model with GPU offload: first single-turn attempt ended with exit code `-1` after `61901 ms`; root cause pending log classification.
- [ ] Confirm actual GTX 1650 usage.
- [ ] Record VRAM.
- [ ] Record RAM.
- [ ] Record GPU layers.
- [ ] Record prompt tokens/s.
- [ ] Record generation tokens/s.
- [ ] Compare CPU vs GPU-offload behavior.

GPU smoke attempt 1 evidence:

- exit code: `-1`
- wall time: `61901 ms`
- post-run GPU snapshot: GTX 1650, `269 MiB` used, `3667 MiB` free, `32%` utilization
- classification: `IN_PROGRESS`; do not treat as model or CUDA failure until stderr is classified.

### 2.4 Runtime gate

- [ ] LOAD = PASS.
- [ ] GENERATION = PASS.
- [ ] CUDA_OFFLOAD = PASS.
- [ ] METRICS_CAPTURE = PASS.
- [ ] NO_UNEXPLAINED_CRASH = PASS.
- [ ] Classify runtime as COMPATIBLE, PARTIALLY_COMPATIBLE, or BLOCKED.

**Phase status:** IN_PROGRESS

---

## Phase 3 — Telemetry baseline

- [ ] Define normalized execution record schema.
- [ ] Capture model, format, quantization, runtime, and runtime version.
- [ ] Capture context length, prompt/generated tokens, and throughput.
- [ ] Capture wall time, peak RAM, peak VRAM, and offload configuration.
- [ ] Capture termination reason and exit code.
- [ ] Record `provider_api_cost = 0`.
- [ ] Keep local compute cost UNKNOWN until measured.
- [ ] Persist raw output and execution configuration.

**Gate:**

```text
METRICS_COMPLETE = PASS
RAW_EVIDENCE_CAPTURED = PASS
```

---

## Phase 4 — Compact model compatibility

Frozen candidate pool:

- L1 Nanbeige4.2-3B
- L2 Qwen3.5-4B
- L3 Granite 4.2 3B
- L4 SWE-Dev-7B (stretch)

For each candidate:

- [ ] Identify compatible format and quantization.
- [ ] Record exact artifact/version/checksum where practical.
- [ ] Load and generate.
- [ ] Test GPU offload.
- [ ] Measure RAM, VRAM, throughput, and context behavior.
- [ ] Test tool-compatible output.
- [ ] Unload cleanly.
- [ ] Classify COMPATIBLE, PARTIALLY_COMPATIBLE, or BLOCKED.

---

## Phase 5 — CodePro to local-runtime plumbing

Target:

```text
CodePro
-> local inference server
-> model
-> response
-> telemetry
```

- [ ] Start local OpenAI-compatible inference endpoint.
- [ ] Add explicit endpoint and model binding.
- [ ] Enforce NO_SILENT_FALLBACK.
- [ ] Add explicit timeout behavior.
- [ ] Separate HTTP, runtime, and model failures.
- [ ] Run end-to-end smoke test.
- [ ] Persist evidence bundle.

---

## Phase 6 — Execution and verifier plumbing

Target:

```text
CodePro
-> scaffold
-> model
-> repository
-> patch
-> tests/commands
-> independent verifier
-> telemetry
```

- [ ] Create isolated task workspace.
- [ ] Record initial repository revision.
- [ ] Support inspect/edit/command operations.
- [ ] Capture diff, stdout, stderr, and tests.
- [ ] Implement independent verification.
- [ ] Persist verifier evidence and final repository state.

---

## Phase 7 — Scaffold compatibility

Frozen pool:

- S1 mini-swe-agent v2
- S2 Agentless
- S3 AutoCodeRover
- S4 OpenHands

For each:

- [ ] Install and record version/commit.
- [ ] Connect to local runtime.
- [ ] Execute trivial repository task.
- [ ] Confirm inspect/edit/command/termination.
- [ ] Capture artifacts and telemetry.
- [ ] Verify patch.
- [ ] Classify compatibility.

---

## Phase 8 — Scaffold screen

Freeze model, tasks, quantization, context, hardware, and runtime. Vary scaffold.

- [ ] Build diverse set of approximately 10–20 tasks.
- [ ] Run S1/S2/S3/S4.
- [ ] Repeat where needed to estimate variance/noise.
- [ ] Measure verified resolution, tokens, calls, retries, replans, wall time,
      context, RAM, VRAM, termination, and verifier evidence.

---

## Phase 9 — Scaffold pruning

Target: `4 candidates -> approximately 2 survivors`.

- [ ] Compare verified resolution and noise.
- [ ] Compare token/call/time cost.
- [ ] Compare RAM/VRAM and operational complexity.
- [ ] Remove non-contributing candidates.
- [ ] Document rejection/defer reasons.
- [ ] Freeze survivors.

---

## Phase 10 — Model screen

With scaffold frozen:

- [ ] Nanbeige4.2-3B.
- [ ] Qwen3.5-4B.
- [ ] Granite 4.2 3B.
- [ ] SWE-Dev-7B if operationally viable.

Question:

```text
WHERE IS EACH MODEL ECONOMICALLY USEFUL?
```

---

## Phase 11 — Quantization / context optimization

- [ ] Compare justified Q4 variants.
- [ ] Test Q5 only if warranted.
- [ ] Measure capability vs RAM/VRAM/throughput.
- [ ] Test baseline/intermediate/larger contexts.
- [ ] Measure KV-cache and truncation effects.

---

## Phase 12 — Code-structure experiments

### M1 — CodeStruct

- [ ] Implement as an isolatable mechanism.
- [ ] A/B without/with CodeStruct.
- [ ] Hold model/scaffold/tasks constant.
- [ ] Measure resolution, context, latency, and complexity.

### Retrieval

- [ ] Agentic-grep baseline.
- [ ] Lightweight structural-index candidate.
- [ ] Compare localization, tokens, time, and verified resolution.

---

## Phase 13 — Difficulty dataset

- [ ] Record task/repo/language characteristics.
- [ ] Record repository size, files touched, localization, tests, context,
      trajectory, first-attempt result, failure type, per-model result, cost.
- [ ] Derive `cheapest_verified_model` only from observed results.
- [ ] Do not assume monotonicity with model size.

---

## Phase 14 — Cascade experiment

```text
small
-> verifier
-> fail
-> medium
-> verifier
-> fail
-> large
```

- [ ] Define escalation conditions from evidence.
- [ ] Run dataset.
- [ ] Measure duplicate work, total cost, and verified resolution.
- [ ] Compare against fixed-model baselines.

---

## Phase 15 — Router experiment

Only if heterogeneous utility is demonstrated.

- [ ] Build task-feature dataset.
- [ ] Test feature signal.
- [ ] Remove unsupported features.
- [ ] Estimate `P(resolve | model, task_features)`.
- [ ] Implement router candidate.
- [ ] Compare held-out against cascade and fixed-model baselines.

---

## Phase 16 — Held-out validation

```text
PRIMARY_GAIN > NOISE
AND
NO_MATERIAL_HELD_OUT_REGRESSION
AND
COST/COMPLEXITY_JUSTIFIED
AND
REPRODUCIBLE
```

- [ ] Create/freeze held-out set.
- [ ] Run baseline and candidate.
- [ ] Repeat as required.
- [ ] Record regressions.
- [ ] Decide KEEP / REMOVE / DEFER.

---

## Phase 17 — Promotion

- [ ] Reproducible evidence.
- [ ] Gain above noise.
- [ ] Cost justified.
- [ ] Complexity justified.
- [ ] No material held-out regression.
- [ ] Documentation/telemetry complete.
- [ ] Failure modes understood.

Final state: PROMOTED, REJECTED, or DEFERRED.

---

## Phase 18 — WSL2 comparison

Deferred until Windows-native baseline is stable.

- [-] Qualify WSL2 GPU/CUDA.
- [-] Qualify llama.cpp Linux/WSL.
- [-] Hold model/quant/context/prompt constant.
- [-] Compare throughput, RAM/VRAM, filesystem behavior, scaffold
      compatibility, and operational complexity.

---

## Phase 19 — Cloud tier

Deferred until local frontier is measured.

- [-] Identify unresolved local tasks.
- [-] Quantify capability gap.
- [-] Test self-hosted cloud GPU if justified.
- [-] Measure real cost and compare with local tiers.

---

## Current execution pointer

```text
PHASE 0   Strategy freeze               COMPLETE
PHASE 1   Windows hardware              COMPLETE
PHASE 2   Runtime qualification         IN_PROGRESS
PHASE 3   Telemetry baseline            NOT_STARTED
PHASE 4   Model compatibility           NOT_STARTED
PHASE 5   CodePro local plumbing        NOT_STARTED
PHASE 6   Execution/verifier plumbing   NOT_STARTED
PHASE 7   Scaffold compatibility        NOT_STARTED
PHASE 8   Scaffold screen               NOT_STARTED
PHASE 9   Scaffold pruning              NOT_STARTED
PHASE 10  Model screen                  NOT_STARTED
PHASE 11  Quant/context optimization    NOT_STARTED
PHASE 12  Structure experiments         NOT_STARTED
PHASE 13  Difficulty dataset            NOT_STARTED
PHASE 14  Cascade                       NOT_STARTED
PHASE 15  Router                        NOT_STARTED
PHASE 16  Held-out validation           NOT_STARTED
PHASE 17  Promotion                     NOT_STARTED
PHASE 18  WSL2 comparison               DEFERRED
PHASE 19  Cloud tier                    DEFERRED
```

Current task:

```text
PHASE 2.1 — llama.cpp Windows runtime

[x] Freeze b11205 / commit 9588757
[x] Select Windows x64 CUDA 13.4 packages
[x] Install/extract runtime
[x] Confirm llama-cli
[x] Confirm CPU backend with model load/generation
[x] Confirm CUDA backend
```
