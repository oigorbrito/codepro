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


## Completed reconciliation record

Repository reconciliation completed through PR #80. Normal roadmap execution resumes at Phase 3.

Canonical correction plan:

```text
docs/reconciliation-roadmap.md
```

```text
RECONCILIATION = DONE
CURRENT_BLOCK = NONE
NORMAL_PHASE_3_PLUS = RESUMED
```

Phase 0-2 completed evidence remains recorded. Reconciliation is `DONE`; normal roadmap execution is resumed.

The correction is selective:

```text
PREVIOUSLY_PROVEN_CAPABILITY
+ CURRENT_USEFUL_WORK
- REGRESSIONS
- DUPLICATION
= RECONCILED_MAIN
```

Do not use a blind revert, force-push, or silent replacement to satisfy this
override.


---

## Phase 0 â€” Strategy / candidate freeze

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

## Phase 1 â€” Windows hardware qualification

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

## Phase 2 â€” Local inference runtime qualification

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
- [x] Record peak process RAM: CPU `1135.6 MiB`; GPU `1214.9 MiB`.
- [-] Separate model load time was not emitted by the selected CLI capture path; total wall time was captured instead (CPU `4335 ms`, GPU `3982 ms`). This is non-blocking for runtime compatibility and remains available for later telemetry refinement.
- [x] Record prompt tokens/s: controlled metrics run `48.3 t/s` (earlier smoke observed `52.2 t/s`).
- [x] Record generation tokens/s: controlled metrics run `16.8 t/s` (earlier smoke observed `16.5 t/s`).

### 2.3 GPU-offload smoke test

- [x] Run the same model with GPU offload. Final single-turn run exited `0`, returned `GPU_OK`, and offloaded `27/27` layers to `CUDA0`.
- [x] Confirm actual GTX 1650 usage: `CUDA0 = NVIDIA GeForce GTX 1650`.
- [x] Record VRAM: baseline `288 MiB`, peak `1194 MiB`, delta `906 MiB`.
- [x] Record peak process RAM: `1214.9 MiB`.
- [x] Record GPU layers: `27/27` offloaded.
- [x] Record prompt tokens/s: controlled metrics run `74.6 t/s`; earlier verbose smoke `0.2 t/s` is retained as non-representative instrumentation-affected evidence.
- [x] Record generation tokens/s: controlled metrics run `63.7 t/s` (earlier smoke observed `36.0 t/s`).
- [x] Compare CPU vs GPU-offload behavior on the same GGUF/configuration: GPU prompt throughput `+54.5%`, generation throughput `+279.2%`, wall time `-8.1%`; GPU used `906 MiB` incremental VRAM and `79.3 MiB` more peak process RAM. Treat as smoke comparison, not a statistical benchmark.

GPU smoke history:

- attempt 1: exit code `-1`, retained as failed diagnostic attempt.
- final single-turn run: exit code `0`, response `GPU_OK`.
- CUDA backend: `CUDA0 = NVIDIA GeForce GTX 1650`.
- model layers: `27/27` offloaded to GPU.
- observed throughput: prompt `0.2 t/s`, generation `36.0 t/s`.
- post-run GPU snapshot: GTX 1650, `284 MiB` used, `3652 MiB` free.
- classification: GPU load/generation/offload PASS; remaining runtime qualification items stay open until RAM/load-time/metrics completeness is captured.

Quantitative smoke measurement (same GGUF/configuration):

- CPU wall time: `4335 ms`
- GPU wall time: `3982 ms`
- CPU peak process RAM: `1135.6 MiB`
- GPU peak process RAM: `1214.9 MiB`
- GPU VRAM baseline / peak / delta: `288 / 1194 / 906 MiB`
- CPU prompt / generation throughput: `48.3 / 16.8 t/s`
- GPU prompt / generation throughput: `74.6 / 63.7 t/s`
- response validation: `True` for CPU and GPU
- comparison: GPU prompt `+54.5%`, generation `+279.2%`, wall time `-8.1%`; peak process RAM `+79.3 MiB`.
- instrumentation caveat: `ExitCode` and separate `LoadTimeMs` were blank in the metrics CSV; do not infer values. Successful controlled GPU single-turn qualification separately recorded exit code `0` and `GPU_OK`.

### 2.4 Runtime gate

- [x] LOAD = PASS.
- [x] GENERATION = PASS.
- [x] CUDA_OFFLOAD = PASS.
- [x] METRICS_CAPTURE = PASS.
- [x] NO_UNEXPLAINED_CRASH = PASS for the finalized qualification path: controlled CPU/GPU runs completed with valid responses; the earlier diagnostic `-1` was not reproduced and had no retained runtime-failure signature.
- [x] Classify runtime as `COMPATIBLE` for Windows-native local inference on the qualified GTX 1650 baseline.

**Phase status:** COMPLETE

---

## Phase 3 — Telemetry baseline

- [x] Define normalized execution telemetry boundary.
  - Generic authority: `arkx.contracts.ExecutionRecord`.
  - Local inference specialization: `LocalInferenceMeasurementRecordV1`.
  - Correlation boundary: `run_id`.
- [x] Capture model, format, quantization, runtime, and runtime version.
- [x] Capture context length, generation limit, prompt throughput, and generation throughput.
- [x] Capture wall time, peak process RAM, GPU VRAM, and offload configuration.
- [x] Capture termination reason and exit code.
- [x] Record `provider_api_cost_usd = 0` for the observed local execution path.
- [x] Keep local compute cost UNKNOWN until measured.
- [x] Persist raw stdout/stderr, normalized recapture, and SHA256 hashes.
- [x] Preserve historical Phase 2 telemetry separately from the Phase 3 controlled recapture.

**Gate:**

```text
METRICS_COMPLETE = PASS
RAW_EVIDENCE_CAPTURED = PASS
```

**Evidence:** `docs/audits/phase3-telemetry-baseline-20260927.md`.

**Phase status:** COMPLETE
---

## Phase 4 â€” Compact model compatibility

Frozen candidate pool:

- L1 Nanbeige4.2-3B
- L2 Qwen3.5-4B
- L3 Granite 4.2 3B
- L4 SWE-Dev-7B (stretch)

For each candidate:

- [x] Identify compatible format and quantization.
- [x] Record exact artifact/version/checksum where practical.
- [x] Load and generate.
- [x] Test GPU offload.
- [x] Measure RAM, VRAM, throughput, and context behavior.
- [x] Test tool-compatible output.
- [x] Unload cleanly.
- [x] Classify COMPATIBLE, PARTIALLY_COMPATIBLE, or BLOCKED.


Candidate classifications:

- [x] L1 Nanbeige4.2-3B: `COMPATIBLE`.
- [x] L2 Qwen3.5-4B: `COMPATIBLE`.
- [x] L3 Granite 4.2 3B: `COMPATIBLE`.
- [x] L4 SWE-Dev-7B stretch: `COMPATIBLE`.

**Gate:**

```text
ARTIFACT_IDENTITY     = PASS
CPU_LOAD_GENERATION   = PASS
GPU_EXECUTION         = PASS
CONTEXT_4096          = PASS
STRUCTURED_OUTPUT     = PASS
CLEAN_UNLOAD          = PASS
COMPATIBLE            = 4/4
```

**Evidence:** `docs/audits/phase4-model-compatibility-20260928.md`.

**Phase status:** COMPLETE

---
## Phase 5 â€” CodePro to local-runtime plumbing

Target:

```text
CodePro
-> local inference server
-> model
-> response
-> telemetry
```

- [x] Start local OpenAI-compatible inference endpoint.
- [x] Add explicit endpoint and model binding.
- [x] Enforce NO_SILENT_FALLBACK.
- [x] Add explicit timeout behavior.
- [x] Separate HTTP, runtime, and model failures.
- [x] Run end-to-end smoke test.
- [x] Persist evidence bundle.

Implementation boundary:

- `src/arkx/local_runtime.py` provides an explicit loopback-only OpenAI-compatible HTTP binding.
- `tools/run_phase5_local_runtime_smoke.py` persists the real local smoke evidence.
- `docs/decisions/0165-local-runtime-http-adapter.md` records the design basis.
- L3 Granite 4.2 3B is the Phase 5 reference fixture only; it is not a product model selection.

**Evidence:** docs/audits/phase5-local-runtime-plumbing-20260928.md.

**Phase status:** COMPLETE

---

## Phase 6 â€” Execution and verifier plumbing

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

- [x] Create isolated task workspace.
- [x] Record initial repository revision.
- [x] Support inspect/edit/command operations.
- [x] Capture diff, stdout, stderr, and tests.
- [x] Implement independent verification.
- [x] Persist verifier evidence and final repository state.

Implementation boundary:

- `src/arkx/isolated_workspace.py` owns exact detached Git worktree isolation.
- `src/arkx/repository_operations.py` owns explicit inspect/edit/command primitives.
- the existing `run_vertical`, command, patch, and verifier boundaries remain authoritative.
- the Phase 6 controlled scaffold is a plumbing fixture only; Phase 7 owns real scaffold/model compatibility.

**Decision:** `docs/decisions/0166-phase6-execution-verifier-plumbing.md`.

**Evidence:** `docs/audits/phase6-execution-verifier-plumbing-20260928.md`.

**Phase status:** COMPLETE

---

## Phase 7 â€” Scaffold compatibility

Frozen pool:

- S1 mini-swe-agent v2
- S2 Agentless
- S3 AutoCodeRover
- S4 OpenHands

For each frozen candidate, execute the compatibility cell as far as the platform/scaffold permits and preserve blockers without substitution:

- [x] Attempt installation and record exact version/commit.
- [x] Attempt explicit local-runtime binding where installation/runtime startup is reachable.
- [x] Execute the frozen trivial repository task where the scaffold reaches execution.
- [x] Capture inspect/edit/command/termination observations where reachable; unknown remains unknown.
- [x] Capture artifacts and telemetry for every reached boundary.
- [x] Invoke the independent verifier only after an observable repository change.
- [x] Classify all four frozen candidates.

Pool identity: `experiments/phase7/scaffold-pool.json`.

Decision: `docs/decisions/0167-phase7-scaffold-pool.md`.

Execution order: S1 -> S2 -> S3 -> S4. Order is operational, not a quality ranking.

Candidate compatibility cells:

- S1 mini-swe-agent v2.4.6: **BLOCKED_WINDOWS_SHELL_PROTOCOL** — model calls/tool calls observed, but Bash-oriented command contract produced no valid Windows-native edit; CodePro correctly stopped at `NO_OBSERVABLE_CHANGE`.
- S2 Agentless: **BLOCKED_MODEL_EDIT_FORMAT** — docs/audits/phase7-s2-agentless-20260928.md.
- S3 AutoCodeRover: **BLOCKED_INSTALLATION_WINDOWS_NATIVE** — docs/audits/phase7-s3-autocoderover-20260928.md.
- S4 OpenHands: **BLOCKED_TIMEOUT** — docs/audits/phase7-s4-openhands-20260928.md.

**Phase status:** COMPLETE — all four frozen scaffold cells classified; compatible survivors = 0; Phase 8 = BLOCKED_BY_NO_COMPATIBLE_SCAFFOLD.

---


## Phase 8 â€” Scaffold screen

Freeze model, tasks, quantization, context, hardware, and runtime. Vary scaffold.

- [ ] Build diverse set of approximately 10â€“20 tasks.
- [ ] Run S1/S2/S3/S4.
- [ ] Repeat where needed to estimate variance/noise.
- [ ] Measure verified resolution, tokens, calls, retries, replans, wall time,
      context, RAM, VRAM, termination, and verifier evidence.

---

## Phase 9 â€” Scaffold pruning

Target: `4 candidates -> approximately 2 survivors`.

- [ ] Compare verified resolution and noise.
- [ ] Compare token/call/time cost.
- [ ] Compare RAM/VRAM and operational complexity.
- [ ] Remove non-contributing candidates.
- [ ] Document rejection/defer reasons.
- [ ] Freeze survivors.

---

## Phase 10 â€” Model screen

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

## Phase 11 â€” Quantization / context optimization

- [ ] Compare justified Q4 variants.
- [ ] Test Q5 only if warranted.
- [ ] Measure capability vs RAM/VRAM/throughput.
- [ ] Test baseline/intermediate/larger contexts.
- [ ] Measure KV-cache and truncation effects.

---

## Phase 12 â€” Code-structure experiments

### M1 â€” CodeStruct

- [ ] Implement as an isolatable mechanism.
- [ ] A/B without/with CodeStruct.
- [ ] Hold model/scaffold/tasks constant.
- [ ] Measure resolution, context, latency, and complexity.

### Retrieval

- [ ] Agentic-grep baseline.
- [ ] Lightweight structural-index candidate.
- [ ] Compare localization, tokens, time, and verified resolution.

---

## Phase 13 â€” Difficulty dataset

- [ ] Record task/repo/language characteristics.
- [ ] Record repository size, files touched, localization, tests, context,
      trajectory, first-attempt result, failure type, per-model result, cost.
- [ ] Derive `cheapest_verified_model` only from observed results.
- [ ] Do not assume monotonicity with model size.

---

## Phase 14 â€” Cascade experiment

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

## Phase 15 â€” Router experiment

Only if heterogeneous utility is demonstrated.

- [ ] Build task-feature dataset.
- [ ] Test feature signal.
- [ ] Remove unsupported features.
- [ ] Estimate `P(resolve | model, task_features)`.
- [ ] Implement router candidate.
- [ ] Compare held-out against cascade and fixed-model baselines.

---

## Phase 16 â€” Held-out validation

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

## Phase 17 â€” Promotion

- [ ] Reproducible evidence.
- [ ] Gain above noise.
- [ ] Cost justified.
- [ ] Complexity justified.
- [ ] No material held-out regression.
- [ ] Documentation/telemetry complete.
- [ ] Failure modes understood.

Final state: PROMOTED, REJECTED, or DEFERRED.

---

## Phase 18 â€” WSL2 comparison

Deferred until Windows-native baseline is stable.

- [-] Qualify WSL2 GPU/CUDA.
- [-] Qualify llama.cpp Linux/WSL.
- [-] Hold model/quant/context/prompt constant.
- [-] Compare throughput, RAM/VRAM, filesystem behavior, scaffold
      compatibility, and operational complexity.

---

## Phase 19 â€” Cloud tier

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
PHASE 2   Runtime qualification         COMPLETE
PHASE 3   Telemetry baseline            COMPLETE
PHASE 4   Model compatibility           COMPLETE
PHASE 5   CodePro local plumbing        COMPLETE
PHASE 6   Execution/verifier plumbing   COMPLETE
PHASE 7   Scaffold compatibility        COMPLETE
PHASE 7R  S4 runtime requalification    IN_PROGRESS
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
PHASE 7R = S4 RUNTIME REQUALIFICATION
ACTIVE_PR = #91
STATUS = IN_PROGRESS / S4-R8_BLOCKED_TREATMENT_NOT_OBSERVED
PHASE 8 = BLOCKED_PENDING_PHASE7R
```
