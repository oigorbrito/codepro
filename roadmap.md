# CodePro Roadmap

This is the living operational roadmap for CodePro.

## Completion discipline

Every implementation task must follow:

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

When an implementation is completed and verified, update this file in the same
change or immediately afterward and mark the corresponding item `[x]`. If the
implementation changes scope, add or revise the relevant roadmap item rather
than silently expanding scope.

## Governing strategy

```text
CANDIDATE_POOL_V0 = FROZEN
LOCAL_FIRST = ACTIVE
PAID_API_DEPENDENCY = OFF_CRITICAL_PATH
ROUTER = NOT_YET_IMPLEMENTED
INITIAL_PLATFORM = WINDOWS_NATIVE
WSL2 = DEFERRED_UNTIL_WINDOWS_BASELINE
```

Primary principle:

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

Primary optimization target:

```text
VERIFIED_CAPABILITY / TOTAL_OPERATIONAL_COST
```

Operational cost includes tokens, money, latency, calls, retries, context,
RAM/VRAM, compute, complexity, failure surface, and maintenance burden.

---

## Phase 0 — Strategy / candidate freeze

- [x] Define LOCAL_FIRST strategy.
- [x] Remove paid APIs from the critical path.
- [x] Freeze CANDIDATE_POOL_V0.
- [x] Separate model, scaffold, runtime, sandbox, verifier, and router concerns.
- [x] Establish benchmark-driven / evidence-driven evaluation.
- [x] Keep router implementation deferred until local evidence exists.
- [x] Choose Windows native as the first qualification platform.
- [x] Create canonical living roadmap at `roadmap.md`.
- [x] Add mandatory roadmap-synchronization rule to `AGENTS.md`.
- [-] WSL2 qualification.
- [-] Docker GPU qualification.

**Phase status:** COMPLETE

---

## Phase 1 — Windows hardware qualification

### 1.1 Inventory

- [x] GPU identified: NVIDIA GeForce GTX 1650, 4 GB VRAM.
- [x] CPU identified: Intel Core i5-10300H, 4 cores / 8 threads.
- [x] RAM identified: 11.87 GB total, 8 GB + 4 GB, 2933 MT/s.
- [x] OS identified: Windows 11 Home x64.
- [x] WSL2 presence confirmed.
- [x] Docker presence confirmed.

### 1.2 NVIDIA driver baseline

Current observed driver during initial inventory: `462.30`.

Qualification target (2026-09-27): NVIDIA GeForce Game Ready Driver `617.14` WHQL, released 2026-09-22 and listed by NVIDIA for GeForce GTX 1650 notebook GPUs.

- [~] Update NVIDIA Windows driver to the qualified current target (`617.14` WHQL).
- [ ] Reboot host.
- [ ] Run `nvidia-smi`.
- [ ] Record driver version, reported CUDA compatibility, VRAM, and idle VRAM.
- [ ] Confirm GTX 1650 is operational after the update.

**Gate:** `WINDOWS_GPU_BASELINE = PASS`

**Phase status:** IN_PROGRESS

---

## Phase 2 — Local inference runtime qualification

Initial runtime candidate:

```text
R1 = llama.cpp
PLATFORM = Windows
STATUS = CANDIDATE
```

### 2.1 Minimal installation

- [ ] Select a reproducible llama.cpp Windows build.
- [ ] Record version / commit.
- [ ] Confirm CPU backend.
- [ ] Confirm CUDA backend.
- [ ] Avoid installing unnecessary components.

### 2.2 CPU smoke test

- [ ] Load a minimal test model.
- [ ] Generate from a trivial prompt.
- [ ] Record RAM.
- [ ] Record load time.
- [ ] Record prompt tokens/s.
- [ ] Record generation tokens/s.

### 2.3 GPU-offload smoke test

- [ ] Run the same model with GPU offload.
- [ ] Confirm actual GTX 1650 usage.
- [ ] Record VRAM.
- [ ] Record RAM.
- [ ] Record GPU layers.
- [ ] Record prompt tokens/s.
- [ ] Record generation tokens/s.
- [ ] Compare CPU vs GPU-offload behavior.

### 2.4 Runtime gate

- [ ] LOAD = PASS.
- [ ] GENERATION = PASS.
- [ ] CUDA_OFFLOAD = PASS.
- [ ] METRICS_CAPTURE = PASS.
- [ ] NO_UNEXPLAINED_CRASH = PASS.
- [ ] Classify runtime as COMPATIBLE, PARTIALLY_COMPATIBLE, or BLOCKED.

---

## Phase 3 — Telemetry baseline

- [ ] Define a normalized execution record schema.
- [ ] Capture model and model format.
- [ ] Capture quantization.
- [ ] Capture runtime and runtime version.
- [ ] Capture context length.
- [ ] Capture prompt and generated tokens.
- [ ] Capture prompt and generation throughput.
- [ ] Capture wall time.
- [ ] Capture peak RAM and peak VRAM.
- [ ] Capture GPU layers / offload configuration.
- [ ] Capture termination reason and exit code.
- [ ] Record `provider_api_cost = 0`.
- [ ] Record local compute cost as UNKNOWN until measured.
- [ ] Persist raw output and execution configuration.

**Gate:**

```text
METRICS_COMPLETE = PASS
RAW_EVIDENCE_CAPTURED = PASS
```

---

## Phase 4 — Compact model compatibility

Candidate pool:

- L1 Nanbeige4.2-3B
- L2 Qwen3.5-4B
- L3 Granite 4.2 3B
- L4 SWE-Dev-7B (stretch)

For each candidate:

- [ ] Identify compatible format and quantization.
- [ ] Record exact artifact/version/checksum where practical.
- [ ] Load.
- [ ] Generate.
- [ ] Test GPU offload.
- [ ] Measure RAM.
- [ ] Measure VRAM.
- [ ] Measure throughput.
- [ ] Test required context.
- [ ] Test tool-compatible output.
- [ ] Unload cleanly.
- [ ] Classify as COMPATIBLE, PARTIALLY_COMPATIBLE, or BLOCKED.

Do not classify candidates as GOOD/BAD at this stage.

---

## Phase 5 — CodePro to local-runtime plumbing

Target path:

```text
CodePro
-> local inference server
-> model
-> response
-> telemetry
```

- [ ] Start a local OpenAI-compatible inference endpoint.
- [ ] Add explicit endpoint configuration.
- [ ] Add explicit model binding.
- [ ] Enforce NO_SILENT_FALLBACK.
- [ ] Add explicit timeout behavior.
- [ ] Capture HTTP, runtime, and model failures separately.
- [ ] Run an end-to-end smoke test.
- [ ] Persist an evidence bundle.

**Gate:**

```text
CODEPRO_LOCAL_INFERENCE = PASS
NO_SILENT_FALLBACK = PASS
```

---

## Phase 6 — Execution and verifier plumbing

Target path:

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
- [ ] Prepare repository checkout and record initial revision.
- [ ] Support inspect/edit/command operations.
- [ ] Capture diff.
- [ ] Capture stdout/stderr.
- [ ] Run tests.
- [ ] Implement independent verification.
- [ ] Persist verifier evidence.
- [ ] Record final repository state.

**Gate:**

```text
EXECUTION_COMPLETE
RAW_EVIDENCE_CAPTURED
VERIFIER_INDEPENDENT
METRICS_COMPLETE
```

---

## Phase 7 — Scaffold compatibility

Frozen scaffold pool:

- S1 mini-swe-agent v2
- S2 Agentless
- S3 AutoCodeRover
- S4 OpenHands

For each scaffold:

- [ ] Install and record version/commit.
- [ ] Connect to the local runtime.
- [ ] Execute a trivial repository task.
- [ ] Confirm inspect.
- [ ] Confirm edit.
- [ ] Confirm command execution.
- [ ] Confirm termination.
- [ ] Capture artifacts and telemetry.
- [ ] Verify resulting patch.
- [ ] Classify compatibility.

---

## Phase 8 — Scaffold screen

Freeze model, tasks, quantization, context, hardware, and runtime. Vary only
the scaffold.

- [ ] Build an initial diverse set of approximately 10–20 tasks.
- [ ] Run mini-swe-agent.
- [ ] Run Agentless.
- [ ] Run AutoCodeRover.
- [ ] Run OpenHands.
- [ ] Repeat where needed to estimate noise/variance.

Measure verified resolution, tokens, tool calls, commands, retries, replans,
wall time, context used, termination reason, RAM, VRAM, and raw verifier
evidence.

---

## Phase 9 — Scaffold pruning

Target:

```text
4 candidates -> approximately 2 survivors
```

- [ ] Compare verified resolution.
- [ ] Compare token/call/time cost.
- [ ] Compare RAM/VRAM.
- [ ] Compare failure surface.
- [ ] Compare operational complexity.
- [ ] Remove candidates without material contribution.
- [ ] Document rejection/defer reasons.
- [ ] Freeze surviving scaffold set.

A scaffold survives when resolution gain exceeds noise, or similar resolution
is achieved with material cost/time/token reduction.

---

## Phase 10 — Model screen

With scaffold fixed, test the surviving compatible model candidates.

- [ ] Nanbeige4.2-3B.
- [ ] Qwen3.5-4B.
- [ ] Granite 4.2 3B.
- [ ] SWE-Dev-7B if operationally viable.

Question:

```text
WHERE IS EACH MODEL ECONOMICALLY USEFUL?
```

Not:

```text
WHICH MODEL WINS?
```

---

## Phase 11 — Quantization and context optimization

Only for surviving model/scaffold combinations.

- [ ] Compare relevant Q4 variants.
- [ ] Test Q5 only where justified.
- [ ] Measure capability loss/gain.
- [ ] Measure RAM/VRAM and throughput.
- [ ] Test baseline/intermediate/larger contexts.
- [ ] Measure KV-cache cost and truncation effects.

---

## Phase 12 — Code-structure experiments

Only after a stable baseline exists.

### M1 CodeStruct

- [ ] Implement as an isolatable mechanism.
- [ ] A/B test without CodeStruct.
- [ ] A/B test with CodeStruct.
- [ ] Hold model/scaffold/tasks constant.
- [ ] Measure resolution, context, latency, and complexity.

### Retrieval

- [ ] Establish agentic-grep baseline.
- [ ] Implement lightweight structural index candidate.
- [ ] Compare localization accuracy.
- [ ] Compare token use.
- [ ] Compare execution time.
- [ ] Compare verified resolution.

---

## Phase 13 — Difficulty dataset

For each task, record task/repo/language characteristics, repository size,
files touched, localization outcome, tests available, context required,
trajectory length, first-attempt outcome, failure type, per-model result, and
per-model operational cost.

- [ ] Build normalized task feature records.
- [ ] Derive `cheapest_verified_model` from observed results.
- [ ] Do not assume monotonicity with model size.

---

## Phase 14 — Cascade experiment

Test:

```text
small
-> verifier
-> fail
-> medium
-> verifier
-> fail
-> large
```

- [ ] Define evidence-backed escalation conditions.
- [ ] Run the difficulty dataset.
- [ ] Measure duplicated work.
- [ ] Measure total cost.
- [ ] Measure verified resolution.
- [ ] Compare against fixed-model baselines.

---

## Phase 15 — Router experiment

Only if heterogeneous model utility is demonstrated.

- [ ] Build task-feature dataset.
- [ ] Test feature signal individually.
- [ ] Remove features without demonstrated value.
- [ ] Estimate `P(resolve | model, task_features)`.
- [ ] Implement first router candidate.
- [ ] Evaluate held-out.
- [ ] Compare against cascade and fixed-model baselines.

---

## Phase 16 — Held-out validation

For every promotable mechanism:

```text
PRIMARY_GAIN > NOISE
AND
NO_MATERIAL_HELD_OUT_REGRESSION
AND
COST/COMPLEXITY_JUSTIFIED
AND
REPRODUCIBLE
```

- [ ] Create held-out set.
- [ ] Freeze it before validation.
- [ ] Run baseline.
- [ ] Run candidate.
- [ ] Repeat as needed.
- [ ] Record regressions.
- [ ] Decide KEEP / REMOVE / DEFER.

---

## Phase 17 — Promotion

A component reaches promotion only after qualification, measurement,
replication, ablation, held-out validation, and pruning.

- [ ] Evidence is reproducible.
- [ ] Gain is above measured noise.
- [ ] Operational cost is justified.
- [ ] Complexity is justified.
- [ ] No material held-out regression exists.
- [ ] Documentation and telemetry are complete.
- [ ] Failure modes are understood.

Final state: PROMOTED, REJECTED, or DEFERRED.

---

## Phase 18 — WSL2 comparison

Deferred until the Windows-native baseline is stable.

- [-] Qualify GPU access in WSL2.
- [-] Qualify CUDA path in WSL2.
- [-] Qualify llama.cpp Linux/WSL.
- [-] Run same model, quantization, context, and prompt.
- [-] Compare throughput, RAM/VRAM, filesystem behavior, scaffold compatibility,
      and operational complexity.

Question:

```text
DOES WSL PROVIDE MATERIAL VALUE OVER WINDOWS BASELINE?
```

---

## Phase 19 — Cloud tier

Only after the local frontier is measured.

- [-] Identify tasks not resolved by local tiers.
- [-] Quantify capability gap.
- [-] Test self-hosted cloud GPU when justified.
- [-] Measure real cost.
- [-] Compare with local tiers.

Question:

```text
DOES CLOUD UNLOCK VERIFIED CAPABILITY THAT LOCAL TIERS CANNOT PROVIDE
AT JUSTIFIED OPERATIONAL COST?
```

---

## Current execution pointer

```text
PHASE 0   Strategy freeze               COMPLETE
PHASE 1   Windows hardware              IN_PROGRESS
PHASE 2   Runtime qualification         NOT_STARTED
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
PHASE 1.2 — NVIDIA DRIVER

[ ] Update NVIDIA Windows driver
[ ] Reboot
[ ] Capture new nvidia-smi
[ ] Mark Windows GPU baseline complete
```
