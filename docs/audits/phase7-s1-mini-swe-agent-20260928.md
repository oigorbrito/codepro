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

classification = BLOCKED_WINDOWS_SHELL_PROTOCOL
vertical_status = BLOCKED
vertical_reason = NO_OBSERVABLE_CHANGE
mini_exit_status = LimitsExceeded
api_calls = 8
prompt_tokens = 13716
completion_tokens = 798
instance_cost = 0.0

## Candidate gates

EXACT_UPSTREAM_IDENTITY = PASS
INSTALLED_VERSION = PASS
LOCAL_RUNTIME_READY = PASS
MODEL_CALLS_OBSERVED = PASS
INSPECT_OBSERVED = PASS
COMMAND_OBSERVED = PASS
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

Prior diagnostic: the first interactive-CLI attempt was invalidated before the first model call by prompt_toolkit NoConsoleScreenBufferError under captured Windows stdout/stderr. That attempt is preserved under diagnostics and is not a compatibility result.

Evidence: evidence/phase7-scaffold-compatibility/S1-mini-swe-agent/.

Next compatibility cell: S2 Agentless.

## Final S1 root-cause attribution

The headless retest reached the frozen local model and produced 8 model calls, 13,716 prompt tokens and 798 completion tokens.

The trajectory shows Bash-oriented commands (`ls -la`, `cat`, and heredoc syntax) emitted against the Windows-native local environment. Those commands are not valid CMD semantics. The later Python edit command returned zero but produced no observable repository change; CodePro therefore correctly stopped at `NO_OBSERVABLE_CHANGE` and did not invoke the independent verifier.

Final attribution:

S1 = BLOCKED_WINDOWS_SHELL_PROTOCOL
CODEPRO_GATE = CORRECTLY_ENFORCED
MODEL_CALLS = OBSERVED
MODEL_FAILURE = NOT_ESTABLISHED
SILENT_WSL_OR_SHELL_SWITCH = NOT_ALLOWED

This closes the S1 compatibility cell under the frozen Windows-native baseline. WSL2 remains deferred to Phase 18.
