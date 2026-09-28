# Phase 7 S2 - Agentless compatibility audit

Date: 2026-09-28

## Frozen identity

repository = OpenAutoCoder/Agentless
version = v1.5.0
commit = b150f28465a77a81a7f4776384957a4271f5bd69

## Native compatibility contract

Agentless is evaluated as its native repair pipeline, not as a shell agent.
inspect-context -> repair prompt -> OpenAIChatDecoder -> native edit parser -> patch -> CodePro independent verifier

native shell command loop = NOT_APPLICABLE_AGENTLESS_PIPELINE

## Frozen local binding

endpoint = http://127.0.0.1:18090/v1
model_alias = codepro-phase7-granite42-3b
fallback = DISABLED

## Result

classification = BLOCKED_MODEL_EDIT_FORMAT
vertical_status = BLOCKED
vertical_reason = NO_OBSERVABLE_CHANGE
model_calls = 1
prompt_tokens = 355
completion_tokens = 512
adapter_error = None
blocker = None

## Gates

EDIT_OBSERVED = False
EXACT_UPSTREAM_IDENTITY = PASS
EXPLICIT_LOCAL_BINDING = PASS
INDEPENDENT_VERIFIER = False
INSPECT_OBSERVED = PASS
INSTALLATION = PASS
LOCAL_RUNTIME_READY = PASS
MODEL_CALLS_OBSERVED = PASS
NATIVE_EDIT_PARSER_OBSERVED = PASS
PATCH_CAPTURED = False
PYTHON_3_11 = PASS
SOURCE_REPOSITORY_UNCHANGED = PASS
TERMINATION_OBSERVED = PASS
VERIFICATION_COMMAND_OBSERVED = False
WORKSPACE_CLEANUP = PASS

## Semantics

S2 classification closes only the Agentless compatibility cell.
A native pipeline difference is recorded rather than hidden by forcing Agentless into an interactive-shell contract.

AVAILABLE != QUALIFIED
COMPATIBLE != SELECTED
EXECUTED != VERIFIED
VERIFIED != ACCEPTED
NO_SILENT_FALLBACK
NO_SILENT_EXECUTOR_SWITCH

Evidence: evidence/phase7-scaffold-compatibility/S2-Agentless/.

Next compatibility cell: S3 AutoCodeRover.
