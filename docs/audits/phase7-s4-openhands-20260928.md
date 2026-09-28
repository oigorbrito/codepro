# Phase 7 S4 - OpenHands compatibility audit

Date: 2026-09-28

## Frozen identity

repository = OpenHands/OpenHands
agent_canvas_version = 1.21.0
commit = fc6d890f7b21c71a17de60d50597c00355e235ea
agent_server_version = 1.49.3
automation_version = 1.13.3

## Native contract

Agent Canvas request builder -> Agent Server 1.49.3 -> OpenHands agent tools -> isolated repository -> CodePro verifier

The local LLM binding follows the upstream mock-LLM E2E contract: `openai/<model>` plus explicit `base_url`. The llama.cpp configuration is kept identical to S1/S2: no additional reasoning-mode override.

## Result

classification = BLOCKED_TIMEOUT
vertical_status = BLOCKED
vertical_reason = NO_OBSERVABLE_CHANGE
prompt_tokens = None
completion_tokens = None
blocker = None

## Gates

AGENT_CANVAS_READY = PASS
COMMAND_OBSERVED = False
EDIT_OBSERVED = False
EVENT_EDIT_SIGNAL = False
EXACT_NPM_CI = PASS
EXACT_UPSTREAM_IDENTITY = PASS
EXPLICIT_LOCAL_BINDING = PASS
GENERATED_I18N = PASS
INDEPENDENT_VERIFIER = False
INSPECT_OBSERVED = False
LOCAL_RUNTIME_READY = PASS
MODEL_CALLS_OBSERVED = None
PATCH_CAPTURED = False
SOURCE_REPOSITORY_UNCHANGED = PASS
TERMINATION_OBSERVED = False
VITE_NODE_AVAILABLE = PASS
WORKSPACE_CLEANUP = PASS

## Phase 7 pool closure

candidate_statuses = ['BLOCKED_WINDOWS_SHELL_PROTOCOL', 'BLOCKED_MODEL_EDIT_FORMAT', 'BLOCKED_INSTALLATION_WINDOWS_NATIVE', 'BLOCKED_TIMEOUT']
compatible_survivors = 0

All four frozen scaffold cells are now classified. This does not promote or select a scaffold. Phase 8 remains NOT_STARTED until a post-Phase-7 gate review decides whether the comparative scaffold screen is executable with the surviving pool.

COMPATIBLE != SELECTED
EXECUTED != VERIFIED
VERIFIED != ACCEPTED
NO_SILENT_FALLBACK
NO_SILENT_EXECUTOR_SWITCH

Evidence: evidence/phase7-scaffold-compatibility/S4-OpenHands/.
