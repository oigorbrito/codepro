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

LATEST != BEST
OLDER != INVALID
HISTORICAL_CONTROL != CURRENT_CANDIDATE
INTEGRATED != QUALIFIED

BLOCKED != PASS
NOT_EXECUTED != PASS

NO_SILENT_FALLBACK
NO_SILENT_EXECUTOR_SWITCH
NO_SILENT_SCOPE_EXPANSION
NO_SILENT_VERSION_SUBSTITUTION
```

## Decision rules

1. A component has no tenure. It remains only while current evidence supports its role.
2. A local pass is reported as local evidence, never as scientific signal or upstream evidence.
3. States are not collapsed: hypothesis, implementation, execution, acceptance, and promotion each require their own record.
4. Blocked and not-executed outcomes are first-class outcomes and cannot be reported as passes.
5. Any fallback, executor change, scope change, or version substitution is explicit in the record and review.
6. New architecture requires a decision record describing the observed need, alternatives, evidence, and rollback/removal condition.
7. External executor/runtime versions must have a visible freshness state. A materially stale version may remain as a reproducible historical control, but it cannot silently remain the sole current operational candidate.
8. A newer version is a candidate, not a promotion. Upstream release or benchmark evidence justifies local requalification, not adoption by assertion.

## Current product boundary

This repository defines deterministic task characterization, progress assessment, rule-based routing/escalation, repository planning artifacts, patch verification, handoff accounting, and empirical-study contracts.

It does not yet define multi-agent execution, concrete executor invocation/orchestration, or product integrations with OpenHands, ReX, mini-SWE-agent, SWE-agent, or other executors. Executor-specific mechanisms remain outside the core until an experiment justifies promotion.

## Version freshness

Version freshness is governed by `docs/version-freshness-policy.md`.

The policy distinguishes current stable candidates, near-current versions, materially stale versions requiring requalification, historical controls, and unresolved version identities. Freshness review is observational and never substitutes for CodePro qualification.
