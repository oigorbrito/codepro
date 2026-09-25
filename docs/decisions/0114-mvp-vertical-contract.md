# Decision 0114 — MVP vertical operational contract

## Status

M0 contract proposal; implementation and executor selection are pending.

## Goal

Define the smallest real user journey that can become a private operational
MVP. The journey uses one authorized repository, one task class, one explicitly
selected executor and one acceptance authority.

## Required input

The request must identify:

- task and immutable repository revision;
- authorized workspace and requested scope;
- task instruction;
- acceptance command or declared acceptance authority;
- executor identity and configuration;
- budget and wall-time limit;
- evidence destination and retention policy.

## Required output

One immutable execution record must contain:

- request, plan and executor identities;
- provider/model/sandbox identities when used;
- command/result or structured environment error;
- artifacts and raw output references;
- verification state and evidence;
- acceptance decision and authority;
- terminal state: completed, failed, timeout or blocked.

No missing identity, missing evidence or blocked infrastructure may become
success. No executor switch, scope expansion or retry may be implicit.

## Current gap

The chassi already provides useful neutral contracts for request, budget,
execution result, verification and acceptance. It does not yet expose one
vertical path binding workspace, scope and acceptance commands to a real
execution. `FakeExecutor` remains a contract-test fixture only and cannot
satisfy the MVP.

## Falsifiable acceptance criteria

M0 is complete only when a local end-to-end run with one real executor can:

1. reject an unauthorized scope before execution;
2. execute the declared task in the declared workspace;
3. enforce the declared budget and wall time;
4. persist raw execution and environment evidence atomically;
5. verify the declared acceptance command;
6. return explicit success, failure, timeout and environment-error states;
7. reproduce the same input identity without overwriting the prior attempt.

Until these criteria pass, the MVP remains `NO-GO`.
