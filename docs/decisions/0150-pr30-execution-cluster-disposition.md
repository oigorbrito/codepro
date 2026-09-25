# Decision 0150 — PR30 execution cluster disposition

Date: 2026-09-25

## Decision

For this integration, the current `main` governed execution spine remains the
authority. The PR30 execution/harness cluster is **not integrated** because no
lossless adapter exists between its `ExecutionResult` lifecycle contract and
`main`'s `CommandResult` observation contract.

This is a disposition of the stale PR30 cluster, not a claim that either
contract is universally superior. The choice follows the repository's current
baseline and avoids replacing an accepted authority with an unqualified,
semantically different runtime.

## Scope retained

The pure, provider-free contract tranche remains eligible for a separate
change: `composition`, `configuration`, `outcomes`, `p82_editing`,
`p82_localization`, and `executor_qualification`, with their referenced
fixtures. It passed 41/41 focused tests in a clean `origin/main` worktree.

## Scope excluded

Do not integrate the PR30 versions of `contracts`, `telemetry`, `handoff`,
`planning`, `routing`, `acceptance`, `promotion`, `recovery`, `execution`,
`harness`, `integration`, `orchestration`, `event_log`, `verifier`, or
`p82_baseline` through this merge effort. Several regress validation or depend
on the unresolved execution cluster.

## Evidence limitation

The native `main` provider-free suite ran in a clean worktree with 71 passed,
1 skipped, and 7 Windows temporary-directory permission failures. The latter
are environment evidence and do not change the architectural disposition.

No provider was called, no product code was changed, and no promotion or
commit/push was authorized by this decision.
