# 0004 — Rule-based routing and evidence-based escalation

- Status: executed with synthetic fixtures
- Date: 2026-09-22

## Context

P1 provides a structural task hypothesis and P2 observes progress. A limited policy can now select an initial path and propose bounded escalation without selecting an executor or taking execution authority.

## Decision

Implement closed contracts for routing and escalation. Route directly from P1 scope, require qualification for unknown input, use a monotonic three-path ladder, require P2/evidence justification for escalation, and enforce explicit attempt/path-escalation budgets.

## Consequences

- Decisions are deterministic and serializable.
- `ESCALATE` is a proposal, not an executor invocation.
- The policy cannot produce `PASS`, change acceptance, retry, replan, or switch executors.
- Budget exhaustion and invalid transitions fail closed.
- No concrete executor or donor dependency is introduced.

## Revisit when

Empirical execution evidence justifies a separate policy review for retry/replan, executor mapping, or richer verification. Those are not P3 changes.

