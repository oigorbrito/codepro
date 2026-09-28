# 0165 - Explicit local-runtime HTTP adapter

Status: ACTIVE FOR PHASE 5

## Decision Basis

\`\`\`text
problem_class = local inference transport integration
decision = add one dependency-free, explicit loopback HTTP adapter bound to one exact model alias
basis_type = UPSTREAM_IMPL + PROJECT_INVARIANT + LOCAL_EVIDENCE
basis_ref = ggml-org/llama.cpp@95887577ab5fead779581a7030a83c7752ff3234 tools/server/README.md; docs/project-contract.md; docs/audits/phase4-model-compatibility-20260928.md
supported_claim = frozen llama-server exposes /v1/health, /v1/models, and /v1/chat/completions; --alias controls API model identity; CodePro forbids silent fallback; Phase 4 established local compatibility for the frozen model pool
applicability = Phase 5 requires the smallest explicit CodePro -> local server -> model -> response path without introducing an executor or provider SDK
deviation = none
\`\`\`

## Decision

Add \`arkx.local_runtime\` as transport plumbing only.

The binding is explicit and fail-closed:

\`\`\`text
loopback /v1 endpoint
+ exact model alias
+ explicit timeout
+ fallback disabled
\`\`\`

Before each chat request, the adapter checks \`/v1/health\` and \`/v1/models\`
and requires the configured model alias to be present exactly. It never
substitutes the first available model and never changes endpoints.

Failure classification remains local to this adapter:

\`\`\`text
HTTP      = transport or HTTP boundary failure
RUNTIME   = local server health/load failure
MODEL     = exact model binding/response identity failure
TIMEOUT   = explicit request deadline exceeded
PROTOCOL  = invalid JSON or response shape
\`\`\`

These categories do not replace the generic CodePro execution/error contracts
and do not imply task verification or acceptance.

## Phase 5 reference fixture

The Phase 5 real smoke freezes L3 Granite 4.2 3B under a dedicated
\`llama-server\` alias. This is a plumbing fixture, not product model selection:

\`\`\`text
REFERENCE_FIXTURE != SELECTED_MODEL
COMPATIBLE != PROMOTED
\`\`\`

The fixture is justified by existing Phase 4 local compatibility evidence and
its fit within the measured local hardware envelope. Phase 10 remains
responsible for comparative model utility.

## Rejected alternatives

- OpenAI Python SDK: rejected for this phase because the repository currently
  declares no runtime dependencies and stdlib HTTP is sufficient.
- Automatic model discovery/fallback: rejected by \`NO_SILENT_FALLBACK\`.
- New executor abstraction: rejected because Phase 5 is transport plumbing;
  executor/scaffold qualification remains later roadmap work.
- Remote/provider endpoint support: rejected because Phase 5 is local-first and
  paid/provider APIs remain off the critical path.

## Removal / extension condition

Remove this adapter if the selected execution profile later supplies an equally
explicit, evidence-bearing local transport boundary without duplicating
authority. Extend beyond loopback only under a separate decision with
authentication and network-boundary evidence.
