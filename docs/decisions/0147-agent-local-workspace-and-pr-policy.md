# Decision 0147 — Agent local workspace and PR policy

Date: 2026-09-24  
Status: accepted as execution policy  
Classification: `AGENT_WORKFLOW_BOUNDARY`

## Decision

The Codepro execution agent defaults to patch-first work in one task-scoped
workspace and one attempt. Commits, branches, pull requests, merges and
promotion are separate authorized transitions, not automatic consequences of
editing files or passing a local test.

Retries receive new attempt/verifier identities and preserve prior artifacts.
An existing branch or PR for the same task is updated when authorized; the
agent does not create duplicate PRs for retries or additional evidence.

The agent records initial workspace state, preserves unrelated changes, and
reports verification and acceptance separately from Git artifacts.

## Rationale

Agent harnesses commonly separate task instruction, environment, verifier and
oracle/reference solution. SWE-agent also exposes local patch application and
PR opening as distinct options. The policy makes that boundary explicit for
Codepro's local repository workflow and prevents PR accumulation from being
mistaken for task progress or acceptance.

## Acceptance criteria

- The workflow is referenced from `AGENTS.md`.
- Default execution produces a patch/evidence record without requiring a
  commit or PR.
- Retry, commit and PR states remain distinct from verification and acceptance.
- Duplicate PR creation is prohibited unless explicitly authorized.
- No rule authorizes merge, promotion, destructive cleanup or scope expansion.
