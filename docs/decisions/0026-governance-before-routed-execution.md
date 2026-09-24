# ADR 0026 — Governance before routed execution

## Status

Accepted for empirical validation.

## Context

CodePro now has:

- a command observation boundary;
- explicit executor qualification/binding;
- characterization/routing/planning/verification contracts.

It still needs an authority boundary that answers a different question: whether a request is allowed to execute at all, within which scope and budget, in which environment, and under which independent acceptance authority.

Benchmark/task harnesses reinforce two useful patterns:

- SWE-bench task instances are anchored to explicit task/repository/base-commit identity;
- agent runners expose confirmation modes and explicit step/cost/time limits separately from command execution.

References reviewed:

- SWE-bench dataset structure:
  https://github.com/SWE-bench/SWE-bench/blob/main/docs/guides/datasets.md
- mini-SWE-agent CLI confirmation and limit controls:
  https://github.com/SWE-agent/mini-swe-agent/blob/main/src/minisweagent/run/mini.py
- mini-SWE-agent interactive modes:
  https://github.com/SWE-agent/mini-swe-agent/blob/main/docs/usage/mini.md
- mini-SWE-agent limit enforcement:
  https://github.com/SWE-agent/mini-swe-agent/blob/main/src/minisweagent/agents/default.py

These references motivate explicit identity and limits. CodePro does not adopt their interactive runtime as an authorization protocol.

## Decision

Introduce a pure request/governance boundary.

### TaskRequest

Records:

- request identity;
- requester identity reference;
- task reference;
- project reference;
- requested scope;
- required permissions.

### AuthorityGrant

Records:

- grant identity and authority reference;
- request identity being governed;
- authorized scope;
- permissions;
- maximum command count;
- maximum wall time;
- environment reference;
- independent acceptance authority reference;
- evidence references.

A grant may be incomplete to represent genuinely unknown governance information.

### GovernanceDecision

Produces:

- `AUTHORIZED`;
- `BLOCKED`;
- `UNKNOWN`;

with explicit reason codes.

## Semantic rules

- no grant -> `BLOCKED / MISSING_AUTHORITY`;
- grant for another request -> `BLOCKED`;
- absent scope/permissions/budget/environment/acceptance authority -> `UNKNOWN`;
- explicit empty/insufficient scope or permissions -> `BLOCKED`;
- `AUTHORIZED` requires complete scope, permissions, positive budgets, environment, acceptance authority, and evidence;
- non-authorized decisions cannot carry executable budgets/environment authority;
- governance does not select or bind an executor;
- governance does not verify or accept a result.

## Normative invariants

```text
MISSING != DENIED
UNKNOWN != BLOCKED
AUTHORIZED != EXECUTED
AUTHORIZED != ACCEPTED
GOVERNANCE != ROUTING
GOVERNANCE != EXECUTOR_SELECTION
```

## Empirical acceptance

Tests must demonstrate:

- complete authorization;
- missing authority;
- grant/request identity mismatch;
- unknown scope;
- unknown permissions;
- unknown budget;
- unknown environment;
- unknown acceptance authority;
- explicit scope denial;
- explicit permission denial;
- deterministic set ordering;
- invalid requester/request identity rejected;
- invalid budgets rejected rather than coerced;
- evidence required;
- incomplete `AUTHORIZED` construction rejected;
- non-authorized decisions cannot smuggle executable budget;
- serialization contains no executor identity;
- architecture guard prevents governance from depending on routing/qualification/command;
- mutation probe kills removal of scope denial.

## Non-goals

- executor selection;
- capability qualification;
- task execution orchestration;
- interactive confirmation UI;
- identity-provider integration;
- verification;
- acceptance decision implementation;
- promotion.

## Removal condition

Remove or replace this boundary if a simpler mechanism preserves explicit authority, unknown-versus-denied semantics, bounded execution authority, acceptance-authority separation, and executor neutrality.
