# CodePro project contract

## North star

**MINIMUM SUFFICIENT ARCHITECTURE FOR MAXIMUM RELIABLE CAPABILITY**

Architecture is added only when an observed need and evidence justify it. A donor repository, prototype, or mechanism may inform a hypothesis, but it is not a product dependency and does not become an executor by implication.

## Invariants

The following statements are normative and must remain visible in design, implementation, experiments, and review:

```text
NO_COMPONENT_HAS_TENURE

SCIENTIFIC_SIGNAL != LOCAL_PASS
UPSTREAM_EVIDENCE != LOCAL_EVIDENCE
HYPOTHESIS != IMPLEMENTATION
IMPLEMENTATION != EXECUTED
EXECUTED != ACCEPTED
ACCEPTED != PROMOTED

DONOR != PRODUCT_DEPENDENCY
MECHANISM_PASS != EXECUTOR_ADOPTED

BLOCKED != PASS
NOT_EXECUTED != PASS

NO_SILENT_FALLBACK
NO_SILENT_EXECUTOR_SWITCH
NO_SILENT_SCOPE_EXPANSION
```

## Decision rules

1. A component has no tenure. It remains only while current evidence supports its role.
2. A local pass is reported as local evidence, never as scientific signal or upstream evidence.
3. States are not collapsed: hypothesis, implementation, execution, acceptance, and promotion each require their own record.
4. Blocked and not-executed outcomes are first-class outcomes and cannot be reported as passes.
5. Any fallback, executor change, or scope change is explicit in the record and review.
6. New architecture requires a decision record describing the observed need, alternatives, evidence, and rollback/removal condition.

## Current product boundary

This repository defines deterministic task characterization, progress assessment, rule-based routing/escalation, repository planning artifacts, patch verification, handoff accounting, and empirical-study contracts.

It does not yet define multi-agent execution, concrete executor invocation/orchestration, or product integrations with OpenHands, ReX, mini-SWE-agent, SWE-agent, or other executors. Executor-specific mechanisms remain outside the core until an experiment justifies promotion.

