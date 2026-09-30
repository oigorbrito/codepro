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


## L1 artifact identity result

The non-experimental Phase 7Q preflight completed without starting llama.cpp, OpenHands, or any model invocation.

Two local Nanbeige GGUF artifacts were present:

```text
Nanbeige4.2-3B-Q4_K_M-mainline-e31e82d.gguf
bytes = 2574807872
sha256 = FBCE43B8977DD73A86126E85AE0BFE219EF3131498AE7C37571DEA58F3C6AA34

Nanbeige4.2-3B-Q4_K_M.gguf
bytes = 2574807840
sha256 = 99C7BFB88907F7EEE0A04C4314F1C46BCA391819478D8CB90B3E164F09576489
```

The retained Phase 4 evidence unambiguously links the compatible L1 qualification to the mainline artifact:

```text
artifact_repository = iamimmanuelraj/Nanbeige4.2-3B-GGUF
artifact = Nanbeige4.2-3B-Q4_K_M-mainline-e31e82d.gguf
```

The same artifact path appears in the retained context-4096, CPU, GPU, and tool-constrained stdout evidence.

Therefore the identity gate is satisfied:

```text
L1_ARTIFACT_PATH =
D:\projetos\codepro-mini-runtime\models\phase4\L1-Nanbeige4.2-3B\Nanbeige4.2-3B-Q4_K_M-mainline-e31e82d.gguf

L1_ARTIFACT_BYTES = 2574807872

L1_ARTIFACT_SHA256 =
FBCE43B8977DD73A86126E85AE0BFE219EF3131498AE7C37571DEA58F3C6AA34

PHASE4_COMPATIBLE_ARTIFACT_LINKAGE = ESTABLISHED
```

The non-mainline Nanbeige artifact is not selected and must not be substituted silently.

## Phase 7Q-Q1 decision

Authorize one controlled pair-qualification cell:

```text
CELL = S4-L1-Q1
BASE = S4-R10
SOLE TREATMENT = MODEL L3 Granite 4.2 3B -> L1 Nanbeige4.2-3B
```

Frozen L1 identity:

```text
MODEL_ALIAS = codepro-phase7q-nanbeige42-3b
MODEL_PATH = D:\projetos\codepro-mini-runtime\models\phase4\L1-Nanbeige4.2-3B\Nanbeige4.2-3B-Q4_K_M-mainline-e31e82d.gguf
MODEL_BYTES = 2574807872
MODEL_SHA256 = FBCE43B8977DD73A86126E85AE0BFE219EF3131498AE7C37571DEA58F3C6AA34
```

Everything else remains frozen from S4-R10:

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

Compatibility still requires the unchanged fail-closed gates: exact model identity, local binding, observed model calls, inspect/edit/command, exact patch capture, independent verifier, source repository unchanged, and workspace cleanup.

No S4-L2 or other Phase 7Q cell is authorized by this decision.


## S4-L1-Q1 pre-execution environment failure

The first local Q1 invocation did not enter the runner because the selected Python 3.12 environment failed importing the standard-library `select` extension:

```text
ImportError: DLL load failed while importing select:
Uma política de Controle de Aplicativo bloqueou este arquivo.
```

A second invocation entered the runner, completed the upstream/npm preflight, and then the frozen llama.cpp server exited before readiness:

```text
exit code = 3236495362
hex = 0xC0E90002
classification = BLOCKED_HARNESS_OR_ENVIRONMENT
adapter = null
vertical = null
```

Windows reports `0xC0E90002` as an Application Control policy block. Because no Agent Canvas conversation, model call, repository action, patch, or verifier execution occurred, this is not a valid S4-L1-Q1 experimental result.

Therefore:

```text
S4-L1-Q1_RESULT = NOT_ESTABLISHED
FAILURE_CLASS = HARNESS_ENVIRONMENT
PRIMARY = WINDOWS_APPLICATION_CONTROL_BLOCK
PROMOTION = NOT_AUTHORIZED
S4-L2 = NOT_AUTHORIZED
```

No security policy relaxation is authorized by Phase 7Q.

The next authorized action is read-only diagnosis of the Windows Code Integrity operational log using:

```powershell
uv run --python 3.12 --no-project python .\tools\run_phase7q_windows_application_control_diagnostic.py
```

This diagnostic performs no policy changes and must be used only to identify the exact blocked file(s) and event IDs before deciding whether the environment can be repaired without changing experimental semantics.


## Windows Code Integrity root cause

The read-only Code Integrity diagnostic established the blocked runtime component exactly.

Observed Windows Code Integrity events:

```text
process =
D:\projetos\codepro-mini-runtime\downloads\llama-b11205-bin-win-cuda-13.4-x64\llama-server.exe

blocked module =
D:\projetos\codepro-mini-runtime\downloads\llama-b11205-bin-win-cuda-13.4-x64\llama-server-impl.dll

event IDs = 3077 and 3033
policy ID = {0283ac0f-fff1-49ae-ada1-8a933130cad6}
reason = module did not meet Enterprise signing level requirements or violated code integrity policy
```

The diagnostic also observed the same Code Integrity policy blocking the uv-managed Python 3.12 standard-library extension:

```text
python.exe -> DLLs\select.pyd
event IDs = 3077 and 3033
policy ID = {0283ac0f-fff1-49ae-ada1-8a933130cad6}
```

Therefore the repeated Q1 startup failures are attributable to Windows application-control policy enforcement, not to the L1 Nanbeige model artifact, OpenHands behavior, task semantics, or pair compatibility.

Canonical state:

```text
S4-L1-Q1_RESULT = NOT_ESTABLISHED
FAILURE_CLASS = ENVIRONMENT_DRIFT
PRIMARY = WINDOWS_CODE_INTEGRITY_BLOCKS_FROZEN_RUNTIME_MODULE
BLOCKED_MODULE = llama-server-impl.dll
POLICY_ID = {0283ac0f-fff1-49ae-ada1-8a933130cad6}
MODEL_COMPATIBILITY_CONCLUSION = NOT_REACHED
SCAFFOLD_MODEL_PAIR_CONCLUSION = NOT_REACHED
```

This environment differs materially from the environment in which the same frozen llama.cpp build completed prior Phase 2-7 qualification work.

No security-policy relaxation is authorized. No runtime binary replacement is authorized. Either action would be a new treatment requiring an explicit decision because:

```text
POLICY_CHANGE != ENVIRONMENT_REPAIR_WITHOUT_SEMANTIC_DELTA
RUNTIME_BINARY_CHANGE != SAME_FROZEN_RUNTIME
```

The next action is read-only identity/signature inspection of the exact blocked frozen runtime files before choosing a new decision stream.


## Frozen runtime signature preflight result

The read-only signature preflight observed the current frozen runtime files as follows:

```text
llama-server.exe
bytes = 9216
sha256 = 66C0EBF7CFF9053EABE208CCF1329AB46BFF5B1663750B4979AEF5C3D32DA555
Authenticode = NotSigned
Zone.Identifier = present

llama-server-impl.dll
bytes = 8916480
sha256 = D1EECF41A8CA5D7BD972FDCFDF69270D2D056363CA66FD2EF1E7F5676DCED77A
Authenticode = NotSigned
Zone.Identifier = present
```

The repository does not preserve historical SHA256 values for these two individual files, so the current bytes cannot yet be proven identical to the earlier successful Phase 2-7 runtime bytes.

Supported conclusion:

```text
RUNTIME_BUILD_PATH = PRESERVED
CURRENT_RUNTIME_BYTES = KNOWN
AUTHENTICODE = NOT_SIGNED
ZONE_IDENTIFIER = PRESENT
WINDOWS_POLICY_BLOCK = CONFIRMED
HISTORICAL_BYTE_IDENTITY = UNKNOWN
```

Do not collapse this into `RUNTIME_IDENTITY_INTACT` or `RUNTIME_IDENTITY_CHANGED` without additional evidence.

The next authorized action is another read-only provenance preflight: inspect the runtime download directory for retained archives, checksums, extraction metadata, or download artifacts that can bind the current extracted files back to the frozen b11205 package without changing any file or policy.


## Frozen runtime package provenance result

The read-only provenance preflight found the retained original llama.cpp b11205 package:

```text
archive =
D:\projetos\codepro-mini-runtime\downloads\llama-b11205-bin-win-cuda-13.4-x64.zip

archive_bytes = 152343527
archive_sha256 = D91178299D1007E162ACAD2776A24D5EF8C834A73F3DB282139ADDC12123BD80
archive_zone_identifier = present
```

The extracted target directory is also present and contains the current runtime files with known hashes, including:

```text
llama-server.exe
sha256 = 66C0EBF7CFF9053EABE208CCF1329AB46BFF5B1663750B4979AEF5C3D32DA555

llama-server-impl.dll
sha256 = D1EECF41A8CA5D7BD972FDCFDF69270D2D056363CA66FD2EF1E7F5676DCED77A
```

This establishes retained package provenance at the archive level, but not yet byte-for-byte linkage between the current extracted files and the retained ZIP members.

Current state:

```text
PACKAGE_PROVENANCE = RETAINED
ARCHIVE_IDENTITY = KNOWN
EXTRACTED_RUNTIME_BYTES = KNOWN
ARCHIVE_TO_EXTRACTED_BYTE_LINKAGE = NOT_YET_PROVEN
```

The next authorized action is read-only comparison of the SHA256 of the corresponding members inside the retained ZIP against the current extracted files.
