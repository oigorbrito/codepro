# Decision 0148 — PR30 decomposition and conflict boundary

Date: 2026-09-24; compatibility-gate update: 2026-09-25

## Decision

PR30 must not be merged as a single unit. Its current branch replaces several
foundational `main` contracts and cannot be reconciled safely by choosing one
side of the merge or by concatenating both APIs.

The integration path is decomposed into independently testable tranches. A
tranche may advance only when its imports, tests, and public contract are
compatible with the current `main` baseline.

## Evidence

- A merge simulation from `86b3822499de186a779e9a3887285d92f60fafea` produced
  31 conflicts.
- Conflicts included the package boundary, CLI, contracts, acceptance,
  planning, promotion, recovery, routing, telemetry, verification, tests,
  documentation, and CI workflow.
- The PR30 side replaces or removes current `main` modules including
  `command`, `environment`, `governance`, `project`, `qualification`,
  `provenance`, `spine`, `study`, `treatment`, `validity`, and `workload`.
- Keeping `main`'s foundational modules allowed 109 focused tests to pass.
- The remaining focused write test was blocked by Windows temporary-directory
  permissions, not by a product assertion.
- The combined suite also exposed PR30-only consumers importing contracts that
  no longer exist in `main` (`AcceptancePolicy`, `PromotionDecision`,
  `RecoveryPlan`, and replay/event-log dependencies).
- Unrestricted pytest discovery collected historical `logs/` text artifacts;
  this is a harness/discovery issue, not product evidence.

## Integration tranches

1. **Foundation compatibility gate** — keep `main`'s CLI, command/environment,
   governance, project, qualification, promotion, recovery, and verification
   contracts authoritative. No PR30 implementation enters this tranche without
   an explicit adapter or contract migration.
2. **Passive evidence modules** — evaluate PR30's evidence/provenance and
   read-only records that do not import replaced contracts.
3. **Execution/harness modules** — evaluate `execution`, `harness`,
   `integration`, and `orchestration` together only after their identities,
   lifecycle, and verifier contracts are mapped to `main`.
4. **P82/benchmark experiments** — keep experimental modules and raw evidence
   outside the product core until the preceding tranche has an accepted
   adapter and provider-free tests.
5. **Historical documentation/logs** — preserve as evidence, but do not let
   them participate in test discovery or become implicit product APIs.

## Non-decisions

This record does not delete PR30 files, choose a new executor, promote any
experiment, or authorize a commit/push. The isolated merge was aborted after
the evidence was collected; the main checkout was not changed by the merge.

## Next gate

The next block is the **Foundation compatibility gate**: enumerate the exact
PR30 consumers of each replaced `main` contract and select the first passive
module that can be tested without importing an incompatible contract. If no
such module exists, classify the tranche as blocked rather than creating a
compatibility facade without tests.

## Foundation compatibility result

The symbol audit divides the shared modules into two groups:

### Additive candidates

- `contracts.py` — same core public types; PR30 adds behavior that must be
  checked against `main` validation.
- `telemetry.py` — public surface is equivalent; compare serialization and
  timestamp behavior.
- `handoff.py`, `planning.py`, `routing.py`, and `verification.py` — mostly
  additive or validation differences; eligible for an isolated adapter/merge
  test, one module at a time.

### Semantic conflicts

- `acceptance.py` — independent acceptance authority in `main` versus the
  outcome-policy API in PR30.
- `promotion.py` — frozen promotion gates in `main` versus persisted outcome
  promotion decisions in PR30.
- `recovery.py` — request/controller lifecycle in `main` versus recovery-plan
  and attempt-lineage lifecycle in PR30.
- `cli.py` — read-only inspection/doctor CLI in `main` versus baseline fixture
  CLI in PR30.

The next executable tranche is therefore `contracts.py` only. It must preserve
the `main` validation contract and demonstrate any PR30 additions with focused
tests before `telemetry.py` or the other additive candidates are considered.

## Tranche result

`contracts.py` is **not accepted as an integration candidate** in its current
PR30 form: its diff removes `main`'s constructor, timestamp, numeric, JSON, and
terminal-record validation. A passing happy-path test is insufficient evidence
for that regression.

The first currently viable tranche is instead the **pure contract tranche**:
`composition.py`, `configuration.py`, `outcomes.py`, `p82_editing.py`,
`p82_localization.py`, and `executor_qualification.py`. These modules have no
provider, filesystem, CLI, or runtime side effects; their only internal edge
is `executor_qualification -> composition`. Their focused suite passed 43/43
on Python 3.13 in the PR30 checkout. This is local evidence only; integration
against a clean `main` checkout remains the next required check.

The clean-`main` integration check copied only those six modules, their two
referenced fixtures, and their focused tests into a detached worktree at
`origin/main`. The result was 41/41 passed on Python 3.13. The separate
`test_core_outcomes.py` was not counted because it imports `p82_baseline`, which
belongs to a later execution tranche.

The isolated telemetry gate rejected the PR30 implementation: the canonical
`main` telemetry suite ran 16 tests successfully but failed 4 validation tests
for blank evidence, duplicate task boundaries, events after completion, and
regressive timestamps. The `main` telemetry implementation remains authoritative;
the PR30 version is not an additive candidate in its current form.

The isolated handoff gate also rejected the PR30 implementation: 8 canonical
tests passed and 6 failed on identity/measurement validation, schema version,
duplicate identifiers, and repeated transition accounting. The `main` handoff
contract remains authoritative.

The planning gate could not collect its canonical suite because the PR30
version removes `build_replan_result`, which is part of the current `main`
contract. This is classified as an API incompatibility before behavioral
testing, not as a passing or failing planning result.

The routing gate was also not isolable: importing the PR30 implementation
requires `arkx.integration`, which belongs to the later PR30 execution/harness
architecture and is absent from the `main` baseline. It is therefore deferred
with that architecture tranche rather than pulled in as a hidden dependency.

## Execution/harness dependency gate

The following cluster is not file-isolable because its internal edges cross
the semantic conflicts above:

`configuration -> execution -> harness/integration -> orchestration`, with
`event_log`, `verifier`, `request`, `selection`, `routing`, `promotion`, and
`recovery` as additional contract edges. `p82_baseline` adds further
dependencies on submission and timeout contracts.

This cluster is classified `DEFERRED_ADAPTER_REQUIRED`. Bringing it into
`main` requires one explicit compatibility design for lifecycle, acceptance,
promotion, and recovery identities; copying the files together would merely
hide the conflict and would not constitute qualification.
