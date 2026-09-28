# Phase 7 S1 - mini-SWE-agent compatibility audit

Date: 2026-09-28

## Frozen identity

repository = SWE-agent/mini-swe-agent
version = v2.4.6
commit = a83fcae82d2a08f0ee0c688f9d137b3566c097f8

## Frozen local binding

endpoint = http://127.0.0.1:18089/v1
model_alias = codepro-phase7-granite42-3b
fallback = DISABLED

## Result

classification = RETEST_REQUIRED_ENVIRONMENT_HARNESS
vertical_status = FAILED
vertical_reason = EXECUTOR_EXIT_NONZERO:1
mini_exit_status = None
api_calls = None
prompt_tokens = None
completion_tokens = None
instance_cost = None

## Candidate gates

EXACT_UPSTREAM_IDENTITY = PASS
INSTALLED_VERSION = PASS
LOCAL_RUNTIME_READY = PASS
MODEL_CALLS_OBSERVED = NO
INSPECT_OBSERVED = NO
COMMAND_OBSERVED = NO
EDIT_OBSERVED = NO
TERMINATION_OBSERVED = NO
PATCH_CAPTURED = NO
INDEPENDENT_VERIFIER = NO
SOURCE_REPOSITORY_UNCHANGED = PASS
WORKSPACE_CLEANUP = PASS

## Semantics

S1 classification closes only the mini-SWE-agent compatibility cell.
It does not rank, select, accept, or promote a scaffold.

AVAILABLE != QUALIFIED
COMPATIBLE != SELECTED
EXECUTED != VERIFIED
VERIFIED != ACCEPTED
NO_SILENT_FALLBACK
NO_SILENT_EXECUTOR_SWITCH

If the classification is BLOCKED_MODEL_TOOL_PROTOCOL, the observed blocker belongs to the frozen model/server tool-call protocol and must not be rewritten as a mini-SWE-agent implementation failure.

Evidence: evidence/phase7-scaffold-compatibility/S1-mini-swe-agent/.

Next compatibility cell: S2 Agentless.

## Reconciliation note

The first S1 run is not a valid scaffold compatibility result.

Raw executor evidence shows `prompt_toolkit.output.win32.NoConsoleScreenBufferError` before the first model call because the interactive `mini` CLI was executed under captured Windows stdout/stderr.

Therefore:

INFRA_FAILURE != MODEL_FAILURE
NO_MODEL_CALL != SCAFFOLD_INCOMPATIBLE

Disposition: archive the first run as diagnostic evidence and retest the same pinned mini-SWE-agent through its native headless DefaultAgent/LocalEnvironment/LitellmModel API.
