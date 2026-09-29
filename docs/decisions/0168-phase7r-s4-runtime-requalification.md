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


## S4-R1 log attribution

The local evidence analyzer reported:

```text
context_or_kv_pressure_observed = false
Context size has been exceeded = 0
failed to find free space in the KV cache = 0
failed to find a memory slot = 0
decode() failed = 0
Conversation lease lost = 1
```

Therefore the original S4 context/KV failure signature did not persist under `parallel=1`. Because the conversation still timed out, the next diagnostic target is the Agent Server conversation lifecycle.

This does not authorize a second treatment. The S4-R1 configuration is repeated unchanged only to improve observability. The diagnostic harness records each polling snapshot and captures conversation info/events even when the 240-second polling budget expires.

Run:

```powershell
uv run --python 3.12 --no-project python .\tools\run_phase7r_s4_conversation_diagnostic.py
```

Diagnostic evidence root:

```text
evidence/phase7r-s4-runtime-requalification/S4-OpenHands-parallel1-diagnostic/
```


## Conversation-state diagnostic finding

The instrumented diagnostic repeat remained `running` for the full polling budget while `runtime_status=available` and `can_resume=true`. The last captured conversation info also contained a default-model response latency entry with a non-empty `chatcmpl-...` response id, despite zero accumulated token usage. This is model-call evidence; zero token accounting must not be interpreted as no call.

The attempted event queries were invalid for Agent Server 1.49.3: the endpoint rejected `limit=200` (maximum 100) and `TIMESTAMP_ASC` (accepted values include `TIMESTAMP` and `TIMESTAMP_DESC`). The harness now uses `limit=100&sort_order=TIMESTAMP` and bash `limit=100`.

No second treatment is authorized. Repeat the same S4-R1 configuration only to capture valid events and identify the last agent lifecycle event.


## S4-R1 event-level root cause

Corrected event capture exposed the first concrete agent failure:

```text
kind = ConversationErrorEvent
code = AttributeError
detail = 'PromptTokensDetailsWrapper' object has no attribute 'cache_creation_tokens'
```

This occurred after the Agent Server recorded a non-empty model response id and response latency, but before any repository tool action produced a change. The conversation then emitted a `CondensationRequest` and remained `running` until the external polling timeout.

This signature matches the upstream OpenHands software-agent-sdk telemetry bug documented for LiteLLM >= 1.95.1. The upstream report identifies 1.94.3 and earlier as unaffected and recommends either defensive `getattr` in SDK telemetry or temporarily constraining LiteLLM below 1.95.

## S4-R2 decision

Authorize one new controlled cell:

```text
CELL = S4-R2
BASE = S4-R1
AGENT_SERVER = 1.49.3
LITELLM = 1.94.3
CONSTRAINT_MECHANISM = UV_CONSTRAINT
PARALLEL = 1
CTX_SIZE = 4096
MODEL = unchanged
SCAFFOLD = unchanged
PLATFORM = WINDOWS_NATIVE
FALLBACK = DISABLED
TASK = unchanged
```

The Agent Canvas upstream source is not modified. `UV_CONSTRAINT` is inherited by the upstream `uvx` Agent Server launch and constrains only dependency resolution for the ephemeral tool environment.

Run:

```powershell
uv run --python 3.12 --no-project python .\tools\run_phase7r_s4_litellm_requalification.py
```

Evidence root:

```text
evidence/phase7r-s4-runtime-requalification/S4-OpenHands-parallel1-litellm1943/
```

Compatibility still requires observable repository change, captured patch, and independent verifier success. Clearing the telemetry exception alone is not sufficient.


## S4-R2 result

The exact LiteLLM 1.94.3 constraint removed the S4-R1 telemetry `AttributeError`. S4-R2 recorded real token accounting and response ids, but still produced no emitted repository tool action, no edit, no patch, and no independent verifier pass.

Observed default-agent usage before the first condensation:

```text
prompt_tokens = 316
completion_tokens = 3344
per_turn_token = 3660
```

The event stream then entered repeated `CondensationRequest` / `Condensation` cycles while the conversation remained `running`. The first condenser response itself consumed 780 prompt + 3316 completion tokens and reached a 4096-token turn total. This is materially different from S4-R1: telemetry is now healthy enough to prove model execution, while the agent still never emits an `ActionEvent`.

S4-R2 remains `BLOCKED_TIMEOUT` under the frozen classification ordering. Do not reinterpret the external polling timeout as successful tool compatibility.

## S4-R2 response diagnostic

Before any further treatment, repeat S4-R2 unchanged with OpenHands raw completion logging enabled. Completion logging is observability-only and does not change the model, scaffold, task, context, parallelism, LiteLLM constraint, provider, or fallback policy.

Run:

```powershell
uv run --python 3.12 --no-project python .\tools\run_phase7r_s4_r2_response_diagnostic.py
```

The diagnostic must determine whether the first default-model response is:

- free-form text with no tool call;
- malformed or unsupported native tool-call output;
- generation that fails to terminate before consuming the available turn budget;
- or another response-shape failure.

No S4-R3 treatment is authorized until that response evidence is inspected.


## S4-R2 response diagnostic finding

The raw completion evidence changes the attribution materially.

The first successful `usage_id=default` completion was not an agent task turn. It was Agent Server title generation and returned a short conversation title with no tool calls. Immediately afterward, the first real agent request was rejected by llama.cpp before generation because the serialized prompt was larger than the frozen runtime context:

```text
request_tokens = 14820
ctx_size = 4096
result = ContextWindowExceededError
ActionEvent = none
```

The event stream then entered condensation. Condenser generations reached the 4096-token turn limit, and subsequent default-agent retries were again rejected with requests around 9854 tokens against the same 4096-token context. No terminal or file-editor `ActionEvent` was emitted.

Therefore the current primary blocker is not malformed tool-call output. The task-execution turn is not reaching model generation under the frozen 4096-token context.

The empty external `completions/` directory is an observability-path limitation, not loss of completion evidence: `LLMCompletionLogEvent` records in the captured Agent Server event stream contain the request/response/error payloads needed for attribution.

## S4-R3 decision

Authorize one controlled context-only treatment:

```text
CELL = S4-R3
BASE = S4-R2
CTX_SIZE = 16384
PARALLEL = 1
LITELLM = 1.94.3
MODEL = unchanged
SCAFFOLD = unchanged
AGENT_SERVER = unchanged
AUTOMATION = unchanged
PLATFORM = WINDOWS_NATIVE
PROVIDER = unchanged
FALLBACK = DISABLED
TASK = unchanged
```

Rationale: 16384 is the smallest power-of-two runtime context above the observed 14820-token first task request. This is a single-variable treatment. It does not authorize 32768, model changes, prompt surgery, tool filtering, reasoning changes, provider changes, or platform changes.

Run:

```powershell
uv run --python 3.12 --no-project python .\tools\run_phase7r_s4_r3_context_requalification.py
```

Evidence root:

```text
evidence/phase7r-s4-runtime-requalification/S4-OpenHands-parallel1-litellm1943-ctx16384/
```

Acceptance remains unchanged: an observable authorized edit, captured patch, and independent verifier pass are required. Clearing the context error alone is not compatibility.


## S4-R6 observed result

S4-R6 executed on Windows-native with the OpenHands nested conversation worktree disabled while preserving the CodePro `IsolatedGitWorkspace`.

Observed gates:

```text
platform_contract_observed = true
model_calls_observed = true
inspect_observed = true
edit_observed = false
patch_captured = false
independent_verifier = false
termination_observed = true
source_repository_unchanged = true
workspace_cleanup = false
classification = BLOCKED_MODEL_TOOL_PROTOCOL
```

The cell therefore did not qualify S4.

The R6 evidence rejects the hypothesis that the OpenHands nested conversation worktree was the remaining primary cause of the Windows path failure. With `conversation-worktree=false`, the active workspace remained the CodePro-isolated Windows path, but the agent still emitted POSIX/GNU-oriented actions:

```text
find . -name "value.py" -type f
ls -la
```

and then supplied the file editor a POSIX-shaped path:

```text
/projetos/codepro-mini-runtime/.../value.py
```

The file editor rejected that path and suggested the correct `D:\\...` absolute path. The event stream then terminated at `MaxIterationsReached (8)` without an edit.

The captured prompt/tool metadata isolates a remaining internal instruction conflict in the frozen OpenHands stack:

- the CodePro suffix says Windows-native / PowerShell and requires `D:\\...` paths;
- the base system prompt recommends `find`, `grep`, and `sed`;
- the file editor description says absolute paths must start with `/`.

Because the conflict persists after removing the nested worktree, S4-R6 is classified as `BLOCKED_MODEL_TOOL_PROTOCOL`, with the more specific attribution `WINDOWS_TOOL_INSTRUCTION_CONFLICT`.

No S4-R7 treatment is authorized by this result alone. Any next cell must target this isolated instruction conflict as a single documented treatment while keeping model, provider, scaffold identity, task, Windows-native platform, context `16384`, parallel `1`, LiteLLM `1.94.3`, time budgets, and fallback policy frozen.


## S4-R7 decision

S4-R6 isolated the remaining blocker as an instruction-precedence conflict rather than a workspace-isolation defect.

The frozen OpenHands stack presented the model with mutually inconsistent platform instructions:

- the CodePro platform suffix declared Windows-native / PowerShell and required drive-qualified Windows paths;
- the generic OpenHands system prompt still recommended POSIX-oriented commands such as `find`, `grep`, and `sed`;
- the frozen file-editor tool description stated that absolute paths start with `/`.

R6 proved that merely removing the nested OpenHands worktree does not resolve this conflict. It also proved that the Windows contract is transported successfully and observed by the Agent Server.

Authorize one controlled treatment:

```text
CELL = S4-R7
BASE = S4-R6
PLATFORM_CONTRACT = windows-powershell-v1 -> windows-powershell-v2
CONVERSATION_WORKTREE = false
CTX_SIZE = 16384
PARALLEL = 1
LITELLM = 1.94.3
MODEL = unchanged
SCAFFOLD = unchanged
AGENT_SERVER = unchanged
AUTOMATION = unchanged
PLATFORM = WINDOWS_NATIVE
PROVIDER = unchanged
TIME_BUDGETS = 600 / 660 / 720
MAX_ITERATIONS = 8
FALLBACK = DISABLED
TASK = unchanged
```

The sole treatment delta is the content of the existing `agent_context.system_message_suffix`. Version 2 adds an explicit conflict-resolution rule:

- when generic OpenHands prompt/tool text conflicts with the Windows-native contract, the Windows-native contract governs platform syntax and path shape;
- POSIX examples including `find`, `grep`, `sed`, `cat -n`, and the statement that absolute paths start with `/` are declared inapplicable to this Windows-native cell;
- PowerShell-native equivalents and drive-qualified Windows absolute paths are required.

This does not patch the frozen OpenHands checkout, change the toolset, alter the user task, raise the iteration cap, switch provider/model, migrate platform, or enable fallback.

Run:

```powershell
uv run --python 3.12 --no-project python .\tools\run_phase7r_s4_r7_windows_instruction_precedence.py
```

Evidence root:

```text
evidence/phase7r-s4-runtime-requalification/S4-OpenHands-parallel1-litellm1943-ctx16384-timeout600-winps2-single-workspace/
```

R7 is `COMPATIBLE` only if all frozen acceptance gates are true, including observable inspection, edit, exact patch capture, independent verifier pass, terminal observation, source-repository preservation, and workspace cleanup.

If R7 remains blocked, classify the first new blocker from the evidence. Do not increase max iterations, change toolset, patch upstream OpenHands, alter task/model/provider/context/platform, enable fallback, or authorize another cell without a distinct isolated cause.


## S4-R7 observed result

S4-R7 executed on the reconciled Windows-native branch head with the strengthened `windows-powershell-v2` instruction-precedence suffix and with the OpenHands nested worktree still disabled.

Observed gates:

```text
platform_contract_observed = true
model_calls_observed = true
inspect_observed = true
edit_observed = false
patch_captured = false
independent_verifier = false
termination_observed = true
source_repository_unchanged = true
workspace_cleanup = false
classification = BLOCKED_MODEL_TOOL_PROTOCOL
```

The v2 contract was present in the captured system prompt, including the explicit statement that the Windows-native contract governs conflicts and that POSIX examples such as `find`, `grep`, `sed`, `cat -n`, and slash-rooted absolute paths are inapplicable.

Despite that, the first repository actions still used POSIX/GNU syntax:

```text
find /workspace/s4-task -name "value.py" 2>/dev/null || find . -name "value.py" 2>/dev/null
find . -name "value.py" 2>/dev/null
pwd && ls -la
ls -la
```

Only later did the agent issue plain `ls`, which succeeded under PowerShell and exposed `value.py`.

The first file-editor call still used a POSIX-shaped path:

```text
/workspace/s4-task/value.py
```

and the editor rejected it as non-absolute in the Windows runtime.

A later response recognized the correct drive-qualified workspace path, but the generated native tool call for `file_editor` failed JSON validation before execution:

```text
Error validating tool 'file_editor':
Unterminated string ... Arguments: unparseable JSON
```

The conversation then reached `MaxIterationsReached (8)` without an edit.

Attribution:

```text
PRIMARY = WINDOWS_TOOL_PROTOCOL_NONCOMPLIANCE_PERSISTS
SECONDARY = WINDOWS_PATH_NATIVE_TOOL_JSON_ESCAPE_FAILURE
```

The ordering is material. The secondary malformed JSON event occurred only after multiple earlier actions had already ignored the v2 Windows contract. Therefore R7 does not isolate JSON escaping as the sole remaining cause, and it does not justify treating that symptom alone as an authorized next cell.

Conclusion:

- textual precedence in `agent_context.system_message_suffix` is insufficient for this frozen model/scaffold combination;
- S4 remains unqualified;
- no R8 treatment is authorized by R7 alone;
- do not change max iterations, toolset, upstream OpenHands source, task, model, provider, context, platform, or fallback policy without a new isolated causal argument.


## S4-R8 decision

R7 by itself did not authorize a next treatment. A subsequent source-level inspection of the frozen Agent Canvas adapter and the OpenHands SDK configuration boundary supplies the missing isolated causal argument.

The frozen Agent Canvas adapter forwards OpenHands `agent_settings` fields into the Agent Server payload. The OpenHands SDK supports an inline `system_prompt` setting whose documented behavior is to use the supplied text verbatim instead of rendering the default `system_prompt_filename`.

This creates a controlled ablation that does not patch the frozen OpenHands checkout and does not change the toolset: replace only the generic OpenHands base system prompt that contains the observed POSIX guidance. The file-editor tool description remains unchanged, including its slash-rooted absolute-path language. Holding that metadata constant is intentional: R8 measures whether the base system prompt is the dominant source of R7 protocol noncompliance.

Authorize:

```text
CELL = S4-R8
BASE = S4-R7
SYSTEM_PROMPT = default -> windows-minimal-v1
PLATFORM_CONTRACT = windows-powershell-v2
CONVERSATION_WORKTREE = false
CTX_SIZE = 16384
PARALLEL = 1
LITELLM = 1.94.3
MODEL = unchanged
SCAFFOLD = unchanged
OPENHANDS_COMMIT = unchanged
AGENT_SERVER = unchanged
AUTOMATION = unchanged
TOOLSET = unchanged
TOOL_METADATA = unchanged
PLATFORM = WINDOWS_NATIVE
PROVIDER = unchanged
TIME_BUDGETS = 600 / 660 / 720
MAX_ITERATIONS = 8
FALLBACK = DISABLED
TASK = unchanged
```

The inline prompt is deliberately minimal. It states the agent role, asks it to use the provided tools for the requested edit/check workflow, makes the dynamic platform contract authoritative, and requires use of the runtime-reported workspace path. It does not encode the answer to the frozen task and does not alter acceptance criteria.

A new fail-closed gate, `system_prompt_profile_observed`, requires the Agent Server conversation state to expose the expected inline prompt before compatibility can be returned.

Run:

```powershell
uv run --python 3.12 --no-project python .\tools\run_phase7r_s4_r8_inline_system_prompt_ablation.py
```

Evidence root:

```text
evidence/phase7r-s4-runtime-requalification/S4-OpenHands-parallel1-litellm1943-ctx16384-timeout600-winps2-inlineprompt1-single-workspace/
```

Interpretation:

- if POSIX terminal actions disappear but slash-rooted file-editor paths persist, the remaining blocker is isolated to tool metadata/model tool-path handling;
- if both disappear and the edit/verifier gates pass, S4 may qualify subject to all frozen acceptance gates;
- if POSIX terminal actions persist, replacing the base system prompt is insufficient and no further prompt-only treatment is authorized automatically.

No R9 is authorized by this decision.
