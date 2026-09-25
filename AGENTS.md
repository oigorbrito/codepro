# CodePro agent policy

This file defines repository-wide instructions for coding agents. It applies to
the entire repository unless a deeper AGENTS.md explicitly narrows the scope.

## Reference-bound execution

CodePro is fail-closed with respect to execution-changing work.

Before an agent may implement, modify, invoke, promote, or release any behavior
that can affect task execution, executor semantics, orchestration, prompts,
tool surfaces, verification, acceptance, or promotion, the task MUST carry a
Reference Envelope.

Minimum Reference Envelope:

~~~text
reference_profile_ref = <internal decision/spec or frozen external implementation>
reference_profile_revision = <immutable commit/version/hash when available>
reference_evidence_ref = <documentation, benchmark/evaluation record, or accepted evidence>
scope_ref = <authorized CodePro scope/decision>
~~~

The references must be specific enough for a reviewer to determine what
behavior is being adopted and which parts are CodePro-specific integration.

If a required reference is absent, mutable without disclosure, incompatible
with the requested scope, or cannot be resolved:

~~~text
NO_REFERENCE -> NO_EXECUTION
status = BLOCKED_REFERENCE_REQUIRED
~~~

The agent may inspect and report the missing reference. It must not invent the
reference, silently substitute another implementation, expand scope, change
executor, or treat prior local success as authorization.

## Adopt proven execution; own the envelope

For the first operational release, prefer a frozen, externally documented
coding-agent execution profile over a new CodePro-specific reasoning,
planning, tool-selection, or multi-agent loop.

CodePro owns the envelope around execution:

- request and authority;
- scope and budget;
- exact executor/profile binding;
- environment and revision identity;
- raw trajectory and artifact capture;
- verification;
- event log and replay;
- independent acceptance;
- explicit promotion.

The adopted executor owns task-solving behavior inside the frozen profile.
Do not reimplement its reasoning loop unless a separate decision explicitly
authorizes that work.

## Reference identity

A treatment that can affect execution is not identified by a product or model
name alone. Preserve exact references already required by CodePro contracts,
including prompt/tool-surface references and hashes, executor/adapter versions,
environment/revision identity, and evidence references.

~~~text
SAME_NAME != SAME_TREATMENT
LOCAL_PASS != UPSTREAM_EVIDENCE
EXECUTED != ACCEPTED
ACCEPTED != PROMOTED
NO_SILENT_FALLBACK
NO_SILENT_EXECUTOR_SWITCH
NO_SILENT_SCOPE_EXPANSION
~~~

## Repository guidance

Detailed rationale and the external-methodology mapping live in
docs/decisions/0155-reference-bound-execution.md.

This policy does not itself authorize an executor, P8.2 publication, release,
or promotion. Those remain separate decisions with their own references and
acceptance records.
