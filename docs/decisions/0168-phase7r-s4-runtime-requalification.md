# 0168 — Phase 7R S4 runtime requalification

Date: 2026-09-28

## Status

EXECUTED / ATTRIBUTION_PENDING

## Context

Phase 7 closed with zero compatible scaffold survivors. Its four historical cells remain immutable:

- S1: `BLOCKED_WINDOWS_SHELL_PROTOCOL`
- S2: `BLOCKED_MODEL_EDIT_FORMAT`
- S3: `BLOCKED_INSTALLATION_WINDOWS_NATIVE`
- S4: `BLOCKED_TIMEOUT`

Phase 8 therefore remains `BLOCKED_BY_NO_COMPATIBLE_SCAFFOLD`.

The final S4 evidence reached a real Agent Canvas conversation with the exact frozen OpenHands identity and explicit local llama.cpp binding. The Agent Server log later recorded `Context size has been exceeded`; llama.cpp simultaneously reported KV-cache exhaustion while multiple server slots were active. The frozen server command used `-c 4096` and did not explicitly set `--parallel`.

The frozen llama.cpp b11205 CLI exposes `-np, --parallel N` as the server-slot count. This makes server parallelism a directly testable runtime variable without changing scaffold, model, quantization, task, context size, hardware, provider, or fallback policy.

## Decision

Create one controlled requalification cell:

```text
CELL = S4-R1
SCAFFOLD = OpenHands Agent Canvas v1.21.0
OPENHANDS_COMMIT = fc6d890f7b21c71a17de60d50597c00355e235ea
AGENT_SERVER = 1.49.3
AUTOMATION = 1.13.3
MODEL = codepro-phase7-granite42-3b
MODEL_SHA256 = E0406663965846AE22A403456EB826CCCE5F450840491F71952F18A7CB78E7D5
LLAMA_CPP_BUILD = 11205
LLAMA_CPP_COMMIT = 95887577ab5fead779581a7030a83c7752ff3234
CTX_SIZE = 4096
PARALLEL = 1
PLATFORM = WINDOWS_NATIVE
FALLBACK = DISABLED
TASK = SAME_PHASE7_TRIVIAL_EDIT
```

The only intended treatment delta from the final S4 cell is:

```text
llama-server parallel = auto -> 1
```

This is a requalification experiment, not a rewrite of the Phase 7 result.

## Acceptance boundary

`S4-R1 = COMPATIBLE` only if the existing CodePro gates observe:

- explicit local binding;
- model call telemetry;
- repository inspection/tool activity as available;
- an observable edit to the authorized file;
- captured patch;
- successful independent verifier;
- source repository unchanged;
- clean workspace teardown.

A created conversation, successful model call, or timeout clearance alone is not compatibility.

## Failure semantics

If S4-R1 remains blocked:

- do not increase context size silently;
- do not switch model;
- do not switch provider;
- do not switch to WSL/Linux;
- do not add another scaffold;
- do not start Phase 8.

Any next treatment must be separately authorized and documented.

If S4-R1 becomes compatible, Phase 8 is still not started automatically. The new evidence must be reviewed and merged first; only then may the roadmap gate be changed from `BLOCKED_BY_NO_COMPATIBLE_SCAFFOLD` to `NEXT`.

## Tooling

Run:

```powershell
uv run --python 3.12 --no-project python .\tools\run_phase7r_s4_requalification.py
```

Evidence root:

```text
evidence/phase7r-s4-runtime-requalification/S4-OpenHands-parallel1/
```

## Invariants

```text
AVAILABLE != QUALIFIED
COMPATIBLE != SELECTED
EXECUTION != VERIFICATION
VERIFICATION != ACCEPTANCE
ACCEPTED != PROMOTED

NO_SILENT_FALLBACK
NO_SILENT_EXECUTOR_SWITCH
NO_SILENT_SCOPE_EXPANSION
```


## S4-R1 observed result

The controlled `--parallel 1` cell executed and remained `BLOCKED_TIMEOUT`.

Observed summary:

```text
conversation_id = present
explicit_local_binding = true
parallel = 1
edit_observed = false
patch_captured = false
independent_verifier = false
model_calls_observed = unknown
classification = BLOCKED_TIMEOUT
```

This result rejects the claim that setting server parallelism to 1 is sufficient by itself. It does not yet prove whether context/KV pressure persisted, because that attribution requires the S4-R1 runtime logs.

Next action: run `tools/analyze_phase7r_s4_requalification.py` against the local evidence bundle and review `phase7r-analysis.json` before authorizing another treatment.
