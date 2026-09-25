# ADR 0156 — Minimal operational vertical journey

## Status

Accepted for implementation. This does not authorize executor promotion,
provider/model use, release, or activation.

## Context

CodePro already has governance, characterization, routing, executor-binding,
command-observation, verification, and evidence contracts, but the public CLI
does not expose one real end-to-end task execution path.

The release scope requires one narrow operational journey before broader
executor or product claims are justified.

## Decision

Add one explicit local-command vertical journey:

```text
declared request + authority
-> exact Git revision and clean workspace check
-> one explicitly named local-command executor
-> bounded shell-free invocation
-> changed-file scope check
-> one declared verifier command
-> append-only/atomic run evidence
-> explicit terminal status
```

The executor command is supplied explicitly by the caller. CodePro does not
select among executors and does not fallback.

The initial implementation uses the existing governed spine and
`LocalCommandEnvironment`; it does not create another orchestration system.

## Decision basis

```text
problem_class = missing operational vertical journey
decision = expose one bounded, explicit, evidence-producing execution path
basis_type = PROJECT_INVARIANT + LOCAL_EVIDENCE
basis_ref =
  docs/mvp-release-scope.md
  docs/release-readiness-plan.md
  arkx.spine.execute_governed
  arkx.command.LocalCommandEnvironment
supported_claim =
  the repository already contains the necessary contracts; the smallest
  product gap is composition into one usable path
applicability =
  operational MVP boundary before provider/model qualification
deviation = none
```

## Non-goals

- no hidden executor choice;
- no multi-executor routing;
- no automatic fallback;
- no model/provider invocation;
- no acceptance or promotion decision;
- no claim that a local command executor is a qualified coding model.

## Evidence rules

Each run has a deterministic run identity and a new evidence directory.
Existing evidence is never overwritten. Before invocation the workspace must be
an exact clean Git revision. After invocation, changed files must remain within
the authorized scope before verification is permitted.
