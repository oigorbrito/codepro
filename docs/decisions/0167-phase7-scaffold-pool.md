# 0167 - Freeze Phase 7 scaffold compatibility pool

Status: ACTIVE FOR PHASE 7

## Decision

Phase 7 freezes four independently implemented scaffolds and qualifies them one
at a time against the already-proven CodePro local-runtime and
execution/verifier boundaries.

The frozen identities are:

```text
S1 mini-swe-agent
   repository = SWE-agent/mini-swe-agent
   version    = v2.4.6
   commit     = a83fcae82d2a08f0ee0c688f9d137b3566c097f8

S2 Agentless
   repository = OpenAutoCoder/Agentless
   version    = v1.5.0
   commit     = b150f28465a77a81a7f4776384957a4271f5bd69

S3 AutoCodeRover
   repository = AutoCodeRoverSG/auto-code-rover
   version    = v1.1.0
   commit     = 1aafff1be4549fff4db9d61bf54bfa8b0669ea57

S4 OpenHands
   repository = OpenHands/OpenHands
   version    = v1.21.0
   commit     = fc6d890f7b21c71a17de60d50597c00355e235ea
```

S1 and S4 preserve prior CodePro evidence continuity. S2 and S3 use stable
upstream releases because the roadmap froze those scaffold families without an
existing CodePro version identity.

## Compatibility protocol

Each candidate is evaluated as one independent block under the narrowest common
contract that can be represented without changing the scaffold implementation:

```text
same CodePro local llama.cpp endpoint
same Phase 7 model fixture
same trivial repository-edit objective
same isolated repository boundary where mechanically possible
same independent CodePro verifier
same evidence/telemetry requirements
```

The minimum candidate result records:

1. exact upstream repository/version/commit;
2. installation/runtime preflight;
3. explicit local endpoint and model binding;
4. one bounded trivial repository task;
5. observable inspect/edit/command/termination behavior or the closest native
   scaffold equivalent;
6. raw stdout/stderr and scaffold artifacts;
7. patch/change capture;
8. independent verifier result;
9. timing/token/call telemetry when observable;
10. explicit compatibility classification and blocker if not compatible.

## Local runtime integration observations

These observations justify attempting the frozen pool; they are not
compatibility results.

- mini-SWE-agent v2.4.6 documents local models through LiteLLM with
  `custom_llm_provider: openai` and `api_base`.
- Agentless v1.5.0 constructs the OpenAI Python client with a `base_url`
  surface, but the exact pinned workflow still needs an explicit local-binding
  validation.
- AutoCodeRover v1.1.0 contains LiteLLM/OpenAI-compatible code paths and a
  generic-model mechanism; its exact local-model/base-URL interaction must be
  proven rather than assumed.
- OpenHands v1.21.0 is Agent Canvas/orchestration. Its frozen
  `config/defaults.json` pins `openhands-agent-server==1.49.3`, and the
  Canvas CLI launches that server through `uvx`. LLM configuration is not a
  Canvas `LLM_BASE_URL` / `LLM_MODEL` environment-variable contract; it is
  carried through Agent Server/Canvas conversation settings. The Phase 7 S4
  runner therefore uses the frozen Canvas request builder with explicit
  `openai/<model>` plus `base_url`, while preserving the prior
  `BLOCKED_RUNTIME` observation only as historical evidence to requalify.

## Ordering

Qualification order is S1 -> S2 -> S3 -> S4.

This ordering does not rank scaffold quality. S1 goes first because CodePro
already has the strongest pinned integration substrate for it, which minimizes
new infrastructure while proving the Phase 7 protocol.

## Semantics

```text
AVAILABLE != QUALIFIED
QUALIFIED != SELECTED_BY_RANK
COMPATIBLE != SELECTED
EXECUTED != VERIFIED
VERIFIED != ACCEPTED
NO_SILENT_FALLBACK
NO_SILENT_EXECUTOR_SWITCH
```

A blocked candidate remains evidence. It must not be silently replaced by
another scaffold or by a different provider/model.

## Phase boundary

Phase 7 establishes compatibility only. Phase 8 performs the comparative
scaffold screen under frozen conditions. Phase 9 performs pruning. No Phase 7
result promotes a scaffold into the product.
