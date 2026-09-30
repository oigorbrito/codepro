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


## Runtime archive linkage result

The read-only archive-member linkage check completed successfully:

```text
archive =
D:\projetos\codepro-mini-runtime\downloads\llama-b11205-bin-win-cuda-13.4-x64.zip

archive_sha256 =
D91178299D1007E162ACAD2776A24D5EF8C834A73F3DB282139ADDC12123BD80

all_targets_match = true
```

Exact member linkage:

```text
llama-server.exe
zip_member_sha256 = 66C0EBF7CFF9053EABE208CCF1329AB46BFF5B1663750B4979AEF5C3D32DA555
extracted_sha256  = 66C0EBF7CFF9053EABE208CCF1329AB46BFF5B1663750B4979AEF5C3D32DA555
byte_identity_match = true

llama-server-impl.dll
zip_member_sha256 = D1EECF41A8CA5D7BD972FDCFDF69270D2D056363CA66FD2EF1E7F5676DCED77A
extracted_sha256  = D1EECF41A8CA5D7BD972FDCFDF69270D2D056363CA66FD2EF1E7F5676DCED77A
byte_identity_match = true
```

Therefore:

```text
PACKAGE_PROVENANCE = ESTABLISHED
ARCHIVE_TO_EXTRACTED_BYTE_LINKAGE = ESTABLISHED
RUNTIME_IDENTITY_INTACT_RELATIVE_TO_RETAINED_PACKAGE = TRUE
RUNTIME_CORRUPTION_OR_LOCAL_SUBSTITUTION = NOT_OBSERVED
```

Combined with the prior Code Integrity events, the supported attribution is now:

```text
Q1_STARTUP_BLOCKER = WINDOWS_APPLICATION_CONTROL_ENVIRONMENT
FROZEN_RUNTIME_BYTES = INTACT
MODEL = NOT_REACHED
SCAFFOLD_MODEL_PAIR = NOT_REACHED
```

No Windows security-policy change, file unblocking, alternate runtime binary, re-extraction treatment, or Q1 retry is authorized by this finding alone.

The next authorized action is read-only inspection of the current Windows application-control posture to determine which active enforcement surface owns Policy ID `{0283ac0f-fff1-49ae-ada1-8a933130cad6}`.


## Application-control posture diagnostic output correction

The first posture-diagnostic run produced an unusably large serialized PowerShell object because unrestricted `Select-Object *` expanded provider/CIM metadata. The captured terminal output was therefore incomplete for policy-owner attribution.

This is a diagnostic-output defect, not an experimental result and not a change in the Windows policy state.

The posture script is constrained to scalar security-state fields, active Code Integrity policy-file metadata, and non-PowerShell registry values only.

Canonical state remains:

```text
POLICY_OWNER_ATTRIBUTION = NOT_ESTABLISHED
Q1_RETRY = NOT_AUTHORIZED
POLICY_CHANGE = NOT_AUTHORIZED
RUNTIME_REPLACEMENT = NOT_AUTHORIZED
```


## Smart App Control policy-owner attribution

The constrained posture diagnostic established the active Windows application-control owner.

Observed local state:

```text
C:\WINDOWS\System32\CodeIntegrity\CiPolicies\Active\{0283AC0F-FFF1-49AE-ADA1-8A933130CAD6}.cip = present
CodeIntegrityPolicyEnforcementStatus = 2
UsermodeCodeIntegrityPolicyEnforcementStatus = 2
VirtualizationBasedSecurityStatus = 2
SecurityServicesRunning = [2]
VerifiedAndReputablePolicyState = 1
SAC_EnforcementReason = 1
```

Microsoft identifies policy ID `{0283ac0f-fff1-49ae-ada1-8a933130cad6}` as the inbox `VerifiedAndReputableDesktop` base policy used when Windows 11 Smart App Control is turned on. Microsoft documents `VerifiedAndReputablePolicyState = 1` as Smart App Control enforcement mode.

Therefore:

```text
POLICY_OWNER = SMART_APP_CONTROL
POLICY_NAME = VerifiedAndReputableDesktop
POLICY_ID = {0283AC0F-FFF1-49AE-ADA1-8A933130CAD6}
UMCI = ENFORCED
CODE_INTEGRITY = ENFORCED
VBS = RUNNING
Q1_STARTUP_BLOCKER = SMART_APP_CONTROL_REJECTION_OF_UNSIGNED_FROZEN_RUNTIME_MODULE
```

The previously observed Event ID 3077 block of `llama-server-impl.dll` is therefore attributable to Smart App Control enforcement, not to runtime corruption, model incompatibility, scaffold behavior, or task semantics.

No Smart App Control disablement, registry mutation, policy removal, file unblocking, runtime replacement, code signing, or supplemental policy deployment is authorized by this attribution.

The next authorized step is read-only `CiTool -lp -json` inventory to capture the active policy's own metadata before deciding whether a security-preserving exception route exists.


## CiTool inventory privilege gate

The first read-only `CiTool.exe -lp -json` inventory attempt returned decimal `2147942405`, which is Windows HRESULT `0x80070005 (Access denied)`.

Therefore the empty policy arrays from that run are not evidence that no policies are active.

Canonical result:

```text
CITOOL_INVENTORY = NOT_ESTABLISHED
FAILURE_CLASS = BLOCKED_BY_PRIVILEGE
FAILURE_DETAIL = ACCESS_DENIED
TARGET_POLICY_ABSENCE = NOT_INFERRED
```

A rerun from an elevated Administrator PowerShell is authorized because the command remains read-only and performs no policy mutation.

The following remain unauthorized:

```text
Q1_RETRY = NOT_AUTHORIZED
SMART_APP_CONTROL_DISABLE = NOT_AUTHORIZED
POLICY_REMOVAL = NOT_AUTHORIZED
SUPPLEMENTAL_POLICY_DEPLOYMENT = NOT_AUTHORIZED
RUNTIME_REPLACEMENT = NOT_AUTHORIZED
```


## CiTool elevated inventory remains access denied

A second read-only `CiTool.exe -lp -json` attempt was run from an Administrator PowerShell and again returned:

```text
returncode = 2147942405
returncode_hex = 0x80070005
failure_class = BLOCKED_BY_PRIVILEGE
failure_detail = ACCESS_DENIED
inventory_established = false
```

This rules out the simple explanation that the first failure was caused only by a non-elevated shell. The Microsoft CiTool reference documents `-lp` / `--list-policies` as the supported policy inventory command.

Canonical result:

```text
CITOOL_INVENTORY = NOT_ESTABLISHED
CITOOL_ACCESS = DENIED_EVEN_FROM_REPORTED_ELEVATED_SHELL
TARGET_POLICY_ABSENCE = NOT_INFERRED
POLICY_OWNER = SMART_APP_CONTROL
```

The next authorized action is read-only token/elevation and direct-command diagnostics. No policy mutation is authorized.


## Effective elevation diagnosis

The direct diagnostic captured the actual access token presented to `CiTool`.

Observed:

```text
mandatory integrity SID = S-1-16-8192 (Medium)
BUILTIN\Administrators = deny-only
local account and member of Administrators = deny-only
CiTool -h = SUCCESS
CiTool -lp -json = 0x80070005 ACCESS_DENIED
```

Microsoft documents that standard/filtered processes run at Medium integrity while elevated processes run at High integrity. A deny-only Administrators SID is consistent with the filtered UAC token rather than the full elevated administrator token.

Canonical result:

```text
EFFECTIVE_ELEVATION = FALSE
SHELL_TOKEN = UAC_FILTERED_MEDIUM_INTEGRITY
CITOOL_ACCESS_DENIED = EXPLAINED_BY_NON_ELEVATED_EFFECTIVE_TOKEN
CITOOL_INVENTORY = NOT_ESTABLISHED
```

The next authorized action is to rerun the same read-only diagnostic from a process whose effective token is High integrity (SID `S-1-16-12288`) and whose Administrators SID is enabled, not deny-only.

No UAC policy changes, Smart App Control changes, Code Integrity changes, or other security relaxation are authorized.


## High-integrity CiTool inventory result

The read-only diagnostic was rerun with an effective High integrity administrator token.

Observed:

```text
integrity SID = S-1-16-12288
BUILTIN\Administrators = enabled
effective_elevation = true
CiTool -lp -json = SUCCESS
```

The active Smart App Control base policy is:

```text
PolicyID = 0283ac0f-fff1-49ae-ada1-8a933130cad6
BasePolicyID = 0283ac0f-fff1-49ae-ada1-8a933130cad6
FriendlyName = VerifiedAndReputableDesktop
IsSystemPolicy = true
IsSignedPolicy = true
IsOnDisk = true
IsEnforced = true
IsAuthorized = true
PolicyOptions includes Enabled:Allow Supplemental Policies
```

An active Microsoft supplemental policy is also present for the same base:

```text
FriendlyName = VerifiedAndReputableDesktopFlightSupplemental
BasePolicyID = 0283ac0f-fff1-49ae-ada1-8a933130cad6
IsSystemPolicy = true
IsSignedPolicy = true
IsEnforced = true
IsAuthorized = true
```

Canonical result:

```text
EFFECTIVE_ELEVATION = TRUE
CITOOL_INVENTORY = ESTABLISHED
POLICY_OWNER = SMART_APP_CONTROL
SMART_APP_CONTROL_BASE = VerifiedAndReputableDesktop
SMART_APP_CONTROL_BASE_SIGNED = TRUE
SMART_APP_CONTROL_BASE_ENFORCED = TRUE
SUPPLEMENTAL_CAPABILITY = PRESENT
```

Microsoft's Smart App Control support guidance states that there is no supported per-app bypass for Smart App Control. If Smart App Control cannot establish reputation, unsigned code is blocked; the security-preserving supported route is a valid code signature. Therefore the generic App Control supplemental-policy capability must not be treated as authorization for a local per-app SAC bypass.

For the frozen Phase7Q runtime:

```text
CURRENT_LLAMA_RUNTIME_SIGNATURE = NOT_SIGNED
CURRENT_LLAMA_RUNTIME_BYTES = FROZEN_AND_LINKED_TO_RETAINED_PACKAGE
PER_APP_SAC_BYPASS = NOT_SUPPORTED
SAC_DISABLEMENT = NOT_AUTHORIZED
LOCAL_ALLOWLIST_TREATMENT = NOT_AUTHORIZED
```

A validly signed runtime would be a distinct runtime-byte treatment and cannot be substituted into Q1 silently.


## Authenticode signing capability preflight result

The read-only local signing-capability preflight completed successfully.

Observed:

```text
code_signing_certificates = []
usable_code_signing_certificate_count = 0
signtool.exe = PRESENT
modifies_files = false
modifies_policy = false
```

Canonical result:

```text
SIGNTOOL_AVAILABILITY = PRESENT
LOCAL_CODE_SIGNING_CERTIFICATE = ABSENT
LOCAL_SIGNING_CAPABILITY = ABSENT
SIGNED_RUNTIME_REMEDIATION = NOT_FEASIBLE_WITH_CURRENT_LOCAL_CREDENTIALS
```

This does not mean signed-runtime remediation is impossible in principle. It means it is not available from the current environment without introducing a new external input, such as a trusted code-signing certificate/private key or a separately supplied already-signed runtime artifact.

Either path would be a distinct treatment and would require explicit authorization, identity capture, provenance, and isolated evidence. It must not be substituted into Q1 silently.

Therefore the current Phase7Q Q1 remains not established and blocked before model/scaffold compatibility is reached:

```text
Q1_RESULT = NOT_ESTABLISHED
BLOCKER = SMART_APP_CONTROL_ENFORCEMENT
RUNTIME_BYTE_DRIFT = NOT_OBSERVED_RELATIVE_TO_RETAINED_PACKAGE
MODEL_PAIR_CONCLUSION = NOT_REACHED
Q1_RETRY = NOT_AUTHORIZED
ENVIRONMENT_REMEDIATION_DECISION = REQUIRED
```


## Authorized signed-runtime remediation treatment

The environment-remediation decision is explicitly authorized for a new, isolated treatment whose objective is to restore execution under Smart App Control without disabling or weakening the control.

Authorization boundary:

```text
REMEDIATION_TREATMENT = AUTHORIZED
TREATMENT_CLASS = SIGNED_RUNTIME
SMART_APP_CONTROL_CHANGE = NOT_AUTHORIZED
POLICY_RELAXATION = NOT_AUTHORIZED
Q1_REUSE = NOT_AUTHORIZED
Q1_RETRY = NOT_AUTHORIZED
RUNTIME_SUBSTITUTION = NOT_AUTHORIZED_UNTIL_CANDIDATE_IDENTITY_AND_SIGNATURE_ARE_ESTABLISHED
```

Current upstream discovery does not establish a suitable signed candidate. The current official llama.cpp release workflow builds and packages Windows artifacts directly and contains no observed `signtool`, Authenticode, or equivalent Windows code-signing step. GitHub release attestations establish provenance, not Windows Authenticode trust for Smart App Control.

Therefore:

```text
OFFICIAL_LLAMA_CPP_RELEASE_ARTIFACTS = AVAILABLE
OFFICIAL_RELEASE_PROVENANCE_ATTESTATION = AVAILABLE
OFFICIAL_RELEASE_AUTHENTICODE_SIGNING = NOT_OBSERVED
SIGNED_RUNTIME_CANDIDATE = NOT_ESTABLISHED
```

Any candidate introduced next must be treated as a distinct runtime identity. Before execution it requires at minimum:

- exact source/provenance,
- archive and extracted SHA-256,
- Authenticode status and signer chain,
- version/build identity,
- byte-level separation from the frozen Q1 runtime,
- isolated evidence directory,
- no silent substitution into Q1.


## R1 signed/reputable upstream runtime candidate

The authorized remediation stream selects one exact upstream candidate for identity/signature preflight only.

Frozen candidate:

```text
CELL = PHASE7Q-ENV-R1
SOLE_TREATMENT = LLAMA_CPP_RUNTIME_BUILD
FROM = b11205
TO = b11295
UPSTREAM_REPOSITORY = ggml-org/llama.cpp
UPSTREAM_COMMIT = 3b3d022b823abaa62a467b26a44e10659e080ee7
RELEASE_PUBLISHED_AT = 2026-09-30T18:50:02Z
ASSET = llama-b11295-bin-win-cuda-13.4-x64.zip
ASSET_BYTES = 152769566
ASSET_SHA256 = 5F2EC28C4DED2986499D6B7B9DBD1FECB6EE7182208F3167C40E8EE3D585D1DC
```

This selection is not a compatibility conclusion and does not promote b11295. It is chosen because it is the current official upstream Windows x64 CUDA 13.4 artifact matching the existing backend family.

All other Q1 dimensions remain frozen. R1 is a remediation preflight, not a Q1 retry.

Authorized next action:

- download the exact upstream asset into an isolated remediation staging directory,
- verify the archive SHA-256 against the GitHub-published digest,
- extract into a separate candidate directory,
- record member SHA-256 and Authenticode state for runtime executables/DLLs,
- do not execute candidate binaries,
- do not replace the frozen b11205 runtime,
- do not change Smart App Control or Code Integrity policy.

Only after identity/signature/reputation-relevant evidence is captured may an execution preflight be considered.


## R1 b11295 identity and Authenticode preflight result

The isolated remediation candidate preflight completed without executing candidate binaries.

Observed:

```text
CELL = PHASE7Q-ENV-R1
TAG = b11295
COMMIT = 3b3d022b823abaa62a467b26a44e10659e080ee7
ARCHIVE_BYTES = 152769566
ARCHIVE_SHA256 = 5F2EC28C4DED2986499D6B7B9DBD1FECB6EE7182208F3167C40E8EE3D585D1DC
ARCHIVE_DIGEST_MATCH = TRUE
RUNTIME_REPLACEMENT = FALSE
CANDIDATE_EXECUTION = FALSE
POLICY_CHANGES = FALSE
```

Critical candidate members:

```text
llama-server.exe
  bytes = 9216
  sha256 = FC7CB1C0252B2A98768EE15F3EA79AE59216243DF7F2D69A07A52A50E2A86762
  Authenticode = NotSigned

llama-server-impl.dll
  bytes = 8945664
  sha256 = B85BB48F0B1E684F0C722568651F23E4F17F49DF69C6332F80011D523A003155
  Authenticode = NotSigned
```

The broader extracted executable/DLL set inspected by the preflight is likewise unsigned. The localized Authenticode StatusMessage text is not used as the classification signal; the structured `Status = NotSigned` field is canonical.

Therefore:

```text
R1_IDENTITY = ESTABLISHED
R1_UPSTREAM_ARCHIVE_INTEGRITY = ESTABLISHED
R1_AUTHENTICODE = NOT_SIGNED
R1_SIGNED_RUNTIME_HYPOTHESIS = REJECTED
R1_SAC_REPUTATION_OR_ISG_HYPOTHESIS = NOT_TESTED
```

Because Smart App Control can also authorize code through reputation/Intelligent Security Graph, unsigned status alone does not establish whether this exact official b11295 artifact will execute on the current machine.

The next authorized action is an isolated execution preflight of the candidate `llama-server.exe --version`, with Code Integrity event capture. This is not a runtime replacement, not a Q1 retry, and does not modify policy.
