# 0169 — Phase 7Q scaffold/model pair qualification recovery

Date: 2026-09-30

## Status

IN_PROGRESS / L1_ARTIFACT_IDENTITY_PREFLIGHT_NEXT / NO_EXPERIMENTAL_CELL_AUTHORIZED

## Context

Phase 7 completed with zero compatible scaffold survivors. Phase 7R then performed a bounded requalification of S4 OpenHands against the frozen L3 Granite 4.2 3B Phase 5 fixture and also closed with no compatible survivor.

The terminal S4-R10 evidence removed the earlier runtime, transport, timeout, and harness ambiguities. The remaining failure was persistent Windows tool-protocol noncompliance under the exact S4 + L3 pair:

- POSIX-shaped terminal commands were still emitted despite a Windows-native PowerShell contract and embedded Windows system prompt;
- slash-rooted file-editor paths were still attempted before recovery;
- the correct source edit was reached;
- post-edit verification attempts were again POSIX-shaped and failed;
- max_iterations=10 was observed and exhausted;
- the independent verifier was therefore not reached;
- S4 remained INCOMPATIBLE.

Phase 8 remains blocked because it requires at least one compatible scaffold execution path before a scaffold screen is meaningful.

Phase 4 independently established runtime compatibility for the frozen compact-model pool:

```text
L1 Nanbeige4.2-3B   COMPATIBLE
L2 Qwen3.5-4B       COMPATIBLE
L3 Granite 4.2 3B   COMPATIBLE
L4 SWE-Dev-7B       COMPATIBLE (stretch)
```

Those Phase 4 classifications are runtime/model-format compatibility only. They are not task-solving selection, ranking, or promotion.

## Decision

Open a new decision stream, Phase 7Q, to test whether compatibility is a property of the exact scaffold/model pair rather than scaffold identity alone.

This is not a continuation of Phase 7R and does not rewrite its result.

The first candidate model is L1 Nanbeige4.2-3B solely because L1 is first in the already frozen Phase 4 candidate order. This ordering is operational and must not be interpreted as a model ranking.

Before any experimental cell is authorized, recover the exact local L1 artifact identity from retained local artifacts/evidence.

Run only the non-experimental preflight:

```powershell
uv run --python 3.12 --no-project python .\tools\run_phase7q_model_artifact_preflight.py
```

The preflight:

- performs no model invocation;
- starts no llama.cpp server;
- starts no scaffold;
- changes no repository files;
- enumerates `D:\projetos\codepro-mini-runtime\models\phase4\**\*.gguf`;
- records path, byte size, and SHA256 for every GGUF;
- searches retained local Phase 4 evidence for references to the frozen model names.

## Gate

No Phase 7Q experimental cell is authorized until the verified mainline-compatible L1 artifact is unambiguously identified.

Required identity evidence:

```text
L1_ARTIFACT_PATH = known
L1_ARTIFACT_BYTES = known
L1_ARTIFACT_SHA256 = known
PHASE4_COMPATIBLE_ARTIFACT_LINKAGE = established
```

If multiple L1-looking artifacts exist and the retained evidence does not disambiguate them, stop at `IDENTITY_AMBIGUOUS`. Do not choose by filename, recency, file size, throughput, or convenience.

## Prospective first experimental cell

Only after the identity gate passes may a separately recorded Phase 7Q cell be authorized with a single treatment:

```text
BASE = S4-R10
SOLE TREATMENT = MODEL L3 Granite 4.2 3B -> L1 Nanbeige4.2-3B
```

Everything else would remain frozen from S4-R10 unless separately documented:

```text
SCAFFOLD = OpenHands Agent Canvas v1.21.0
OPENHANDS_COMMIT = fc6d890f7b21c71a17de60d50597c00355e235ea
AGENT_SERVER = 1.49.3
AUTOMATION = 1.13.3
LLAMA_CPP_BUILD = 11205
LLAMA_CPP_COMMIT = 95887577ab5fead779581a7030a83c7752ff3234
PLATFORM = WINDOWS_NATIVE
SYSTEM_PROMPT_PROFILE = windows-embedded-v1
PLATFORM_CONTRACT = windows-powershell-v2
CONVERSATION_WORKTREE = false
CTX_SIZE = 16384
PARALLEL = 1
LITELLM = 1.94.3
TIME_BUDGETS = 600 / 660 / 720
MAX_ITERATIONS = 10
FALLBACK = DISABLED
TASK = unchanged
TOOLSET = unchanged
TOOL_METADATA = unchanged
BYTECODE_CLEANUP = untracked-python-bytecode-only-v1
```

A model swap would not by itself authorize Phase 8. Compatibility would still require the existing exact patch, independent verifier, source cleanliness, and workspace-cleanup gates.

## Invariants

```text
COMPATIBLE != SELECTED
SELECTED != PROMOTED
AVAILABLE != QUALIFIED
EXECUTION != VERIFICATION
VERIFICATION != ACCEPTANCE
ACCEPTED != PROMOTED

NO_SILENT_FALLBACK
NO_SILENT_EXECUTOR_SWITCH
NO_SILENT_SCOPE_EXPANSION
NO_MODEL_RANKING_FROM_PHASE4_COMPATIBILITY
```
