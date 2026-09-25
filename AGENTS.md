# CodePro agent policy

This file defines repository-wide instructions for coding agents.

## Reference-bound execution

CodePro is fail-closed for execution-changing work.

Before an agent may implement, modify, invoke, promote, or release behavior
that can affect execution, executor semantics, orchestration, prompts, tool
surfaces, verification, acceptance, or promotion, the task MUST resolve a
Reference Envelope:

```text
reference_profile_ref = <internal decision/spec or frozen external implementation>
reference_profile_revision = <immutable commit/version/hash when available>
reference_evidence_ref = <documentation, benchmark/evaluation record, or accepted evidence>
scope_ref = <authorized CodePro scope/decision>
```

If a required reference is absent, unresolved, mutable without disclosure,
or incompatible with the authorized scope:

```text
NO_REFERENCE -> NO_EXECUTION
status = BLOCKED_REFERENCE_REQUIRED
```

The agent may inspect and locate candidate references, but must not invent a
reference, silently substitute another implementation, expand scope, switch
executors, or treat local success as authorization.

## Adopt proven execution; own the envelope

For the first operational release, prefer a frozen, externally documented
coding-agent execution profile over a new CodePro-specific reasoning,
planning, tool-selection, or multi-agent loop.

CodePro owns request/authority, scope/budget, exact profile binding,
environment/revision identity, trajectory/artifact capture, verification,
event log/replay, independent acceptance, and explicit promotion.

The adopted executor owns task-solving behavior inside the frozen profile.
Do not reimplement its reasoning loop unless a separate decision explicitly
authorizes that work.

```text
SAME_NAME != SAME_TREATMENT
LOCAL_PASS != UPSTREAM_EVIDENCE
REFERENCE_PRESENT != QUALIFIED
QUALIFIED != EXECUTED
EXECUTED != VERIFIED
VERIFIED != ACCEPTED
ACCEPTED != PROMOTED
NO_SILENT_FALLBACK
NO_SILENT_EXECUTOR_SWITCH
NO_SILENT_SCOPE_EXPANSION
```

Detailed rationale and external-methodology mapping:
`docs/decisions/0155-reference-bound-execution.md`.

This policy does not authorize an executor, P8.2 publication, release, or
promotion. Those remain separate decisions with their own references and
acceptance records.
