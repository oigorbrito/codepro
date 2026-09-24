# Dependency & Executor Freshness Audit v1

Date: 2026-09-24

Status: INITIAL_AUDIT

Scope: components materially involved in the current executor qualification and local execution work.

## Evidence boundary

This audit separates three things:

1. the version observed in the current CodePro work;
2. the latest stable upstream version known at the audit time;
3. whether CodePro has locally qualified that candidate.

`LATEST_STABLE_KNOWN` does not imply `PROMOTED`.

The public repository snapshot may lag local uncommitted/committed experiment work. Local run artifacts remain authoritative for the exact versions actually executed.

## Initial matrix

| Component | Observed CodePro version/state | Latest stable known at audit | Freshness state | Required action |
| --- | --- | --- | --- | --- |
| mini-swe-agent | 1.1 line used by current qualification work | 2.4.6 | STALE_REQUIRES_REQUALIFICATION | Freeze current version as historical B0; qualify 2.4.6 as C1 before further deep v1-specific optimization |
| SWE-agent | 1.1.0 candidate | 1.1.0 | CURRENT_STABLE | No freshness action; qualification status remains independent |
| OpenHands | 1.21.0 candidate | 1.22.0 | NEAR_CURRENT | Review 1.22.0 delta and re-run minimal configuration qualification if still a candidate |
| Ollama | 0.34.3 | 0.34.3 stable known | CURRENT_STABLE | No freshness action required |
| OpenCode | installed binary reported as 2.0.15 | upstream identity/version mapping not reconciled | VERSION_IDENTITY_UNRESOLVED | Resolve distribution/source before any freshness conclusion |
| qwen2.5-coder:3b | local low-marginal-cost model candidate | newer coding model families exist | HISTORICAL_CONTROL_ONLY / model review required | Retain only as explicit low-cost historical candidate until model comparison is designed |

## Material finding: mini-swe-agent

The gap between the currently exercised mini-swe-agent 1.1 line and upstream 2.4.6 is material enough that CodePro must not continue treating v1.1 as the sole present-day operational candidate without requalification.

This finding is strengthened by upstream changes in areas overlapping the current CodePro blocker class, including execution lifecycle, timeout handling, and environment execution behavior.

This does **not** establish that v2.4.6 resolves the local `environment.execute` hang.

### Required experimental posture

```text
B0 = exact current mini-swe-agent 1.1 pin/revision
C1 = exact mini-swe-agent 2.4.6 pin/revision

FIRST:
compatibility + runtime qualification

THEN, only if comparable:
verified resolution + cost + latency + calls/tokens
```

No promotion is authorized by this audit.

## Current blocker interaction

The current diagnostic evidence places the observed hang after:

```text
provider_response
-> parser
-> action_decision
-> dispatch_start
-> action_start
-> environment.execute
-> [no action_end before external watchdog]
```

Therefore:

- provider failure is not established;
- model failure is not established;
- compaction failure is not established;
- task-specific failure is not established;
- the failure boundary is inside or below environment execution.

Because the upstream version gap includes relevant runtime evolution, extensive repair work specific to the v1.1 line should not outrun the v2.4.6 compatibility qualification.

## Project rule introduced by this audit

A component with `STALE_REQUIRES_REQUALIFICATION` may remain as a frozen historical control, but it cannot silently remain the sole current candidate while new executor-specific optimization work accumulates.

See `docs/version-freshness-policy.md`.

## Follow-up

1. Resolve OpenCode distribution identity.
2. Review the OpenHands 1.21.0 -> 1.22.0 delta if OpenHands remains in the qualification shortlist.
3. Execute mini-swe-agent v2.4.6 compatibility/runtime qualification as a distinct experiment.
4. Do not merge the version change into the frozen Observation Compaction Wave 0.
5. Keep Qualification Run v1 blocked until at least two independently qualifiable executors satisfy the CodePro protocol.
