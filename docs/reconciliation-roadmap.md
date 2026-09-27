# CodePro Reconciliation & Recovery Roadmap

Status: **ACTIVE**

This document is the temporary operational control plan for correcting the
unqualified repository replacement introduced around commit `04a670e` while
preserving useful work added afterward.

It does **not** authorize a blind revert, force-push, history rewrite, executor
promotion, or silent architectural replacement.

## Objective

Build one reconciled CodePro state that preserves proven capabilities from the
pre-`04a670e` line and useful capabilities from the current line.

```text
PREVIOUSLY PROVEN CAPABILITY
+ CURRENT USEFUL WORK
- REGRESSIONS
- DUPLICATION
= RECONCILED MAIN
```


## Non-destructive preservation mandate

This roadmap corrects the deviation introduced by the repository replacement;
it does not authorize deleting useful post-deviation implementation.

All current executor/API/provider integration work must be explicitly
inventoried in R1 and preserved through R2-R4 unless a specific `DROP`
decision is supported by evidence.

Default disposition for useful current implementation:

```text
KEEP
or
MERGE
```

`DROP` is exceptional and requires evidence of one of:

```text
REGRESSION
DUPLICATION
INCOMPATIBILITY
SUPERSESSION_WITH_EQUIVALENT_OR_STRONGER_CAPABILITY
```

Difficulty or effort already invested is not itself proof of correctness, but
working integration behavior, successful provider/API connectivity,
authentication/configuration knowledge, adapter code, preflight logic, and
captured evidence are assets that must not be discarded casually.

For executor/API reconciliation:

```text
PRESERVE USEFUL INTEGRATION
    +
RESTORE LOST GOVERNANCE / QUALIFICATION / VERIFICATION
    =
TARGET
```

The recovery target is therefore not the historical repository and not the
current repository in isolation. It is the smallest reconciled composition
that retains useful new integrations while restoring lost proven controls.


## Operating rules

The correction follows a branch-and-PR workflow. Published `main` history is
preserved. Recovery is selective by capability, not a whole-tree rollback.

```text
RESTORE != BLIND REVERT
OLD_PASS != RECONCILED_PASS
AVAILABLE != QUALIFIED
IMPLEMENTED != VERIFIED
VERIFIED != ACCEPTED
ACCEPTED != PROMOTED
UNKNOWN != ZERO
NO_SILENT_FALLBACK
NO_SILENT_EXECUTOR_SWITCH
NO_SILENT_SCOPE_EXPANSION
```

During this roadmap:

1. work one block at a time;
2. prefer one coherent tranche over many tiny corrective patches;
3. do not start the next implementation block until the current block is
   `DONE`, unless the next action is read-only evidence collection;
4. record evidence before changing a block to `DONE`;
5. do not delete current useful work merely to make restoration easier;
6. do not preserve a newer implementation merely because it is newer;
7. structural conflicts require an explicit `KEEP / RESTORE / MERGE / DROP`
   decision;
8. no executor becomes selected or promoted as a side effect of recovery.

## Status vocabulary

- `NOT_STARTED` â€” no implementation work begun.
- `IN_PROGRESS` â€” authorized block is being reconciled.
- `BLOCKED` â€” gate cannot proceed; reason/evidence must be recorded.
- `DONE` â€” block gate passed with evidence.

A block is `DONE` only after its verification gate passes.

---

## R1 â€” Freeze identities and reconciliation matrix

**Status: DONE**

Purpose: establish the exact recovery boundary before restoring code.

Work as one audit block:

- record `CURRENT_MAIN`;
- record migration commit `04a670e40f5d4ee7eb93a554a745a0bf3cbde8d7`;
- record the exact predecessor/base used for recovery;
- inventory capabilities removed, replaced, retained, and newly added;
- classify each critical capability as `KEEP`, `RESTORE`, `MERGE`, or
  `DROP`;
- explicitly include package/CLI, telemetry, measurement, provenance,
  event-log, governance, qualification, execution, verifier/evidence,
  tests/tools, TypeScript chassis, frontend/server, executor work, provider/API
  bindings, authentication/configuration plumbing, and adapter/preflight work;
- identify which historical evidence remains provenance only versus which
  checks must be rerun after reconciliation;
- preserve the completed Windows/llama.cpp qualification as new independent
  evidence.

Do not restore production code in this block.

### R1 gate

Mark `DONE` only when:

- exact commit identities are recorded;
- the capability matrix covers every critical boundary above;
- no critical deletion is still classified only by assumption;
- each collision has a proposed `KEEP / RESTORE / MERGE / DROP` disposition;
- the next restore tranche is explicitly bounded.

**Evidence / decision record:** `docs/audits/reconciliation-r1-20260927.md`.

---

## R2 â€” Restore the proven operational foundation

**Status: IN_PROGRESS**

Purpose: recover the minimum previously validated operational substrate without
removing useful current work.

Perform as one coherent foundation tranche:

- restore the installable Python/package boundary required by the proven core;
- restore the minimum `src/arkx` contracts required by the operational path;
- restore the corresponding regression tests;
- restore the validation tools required to prove that foundation;
- restore CLI/package behavior only where it was previously part of the
  validated boundary;
- keep React/Vite/Tailwind/current UI work unless an explicit conflict requires
  reconciliation;
- repair CI/check definitions so they test code that actually exists;
- do not restore obsolete modules merely because they existed historically.

### R2 gate

Mark `DONE` only when the reconciled foundation proves, from the repository
root:

- package/build boundary is coherent;
- public CLI contract expected by current documentation either works or has
  been explicitly superseded;
- restored focused tests pass;
- repository foundation checks pass;
- current useful frontend/TS work has not been accidentally removed;
- no whole-tree revert or history rewrite was used.

**Evidence / decision record:** `docs/audits/reconciliation-r2-restore-20260927.md` (verification pending).

---

## R3 â€” Reconcile telemetry, evidence, and local-runtime measurements

**Status: NOT_STARTED**

Purpose: use one canonical telemetry/evidence model rather than parallel old
and new systems.

Perform as one telemetry tranche:

- evaluate the prior `ExecutionRecord` / `TelemetryCollector` as the
  canonical generic execution record;
- restore/reconcile Measurement Contract, Run Manifest/provenance, and Event
  Log boundaries needed by current CodePro invariants;
- integrate the new llama.cpp/local-inference measurements:
  model/repository, GGUF/quantization, runtime build/commit, CPU/CUDA device,
  context, GPU layers, wall time, RAM, VRAM, prompt throughput, generation
  throughput, termination, and raw evidence references;
- preserve `provider_api_cost = 0` only when directly observed by the local
  execution model;
- preserve local compute cost as unknown until measured;
- keep `UNKNOWN != ZERO`;
- remove or demote duplicate telemetry contracts only after equivalent useful
  fields have been integrated;
- bind the Phase 2 CPU/GPU evidence to the reconciled telemetry/provenance
  model without rewriting the original observation.

### R3 gate

Mark `DONE` only when:

- exactly one canonical generic execution-telemetry boundary exists;
- local-inference metrics are represented without losing prior semantics;
- raw evidence references are preserved;
- missing/unknown semantics remain fail-closed;
- telemetry/provenance/event-log focused tests pass;
- the Phase 2 measurements can be represented without fabricated values.

**Evidence / decision record:** pending.

---

## R4 â€” Reconcile real execution, verifier, and executor boundaries

**Status: NOT_STARTED**

Purpose: restore real operational behavior while retaining useful modern
interfaces.

Perform as one execution tranche:

- restore/reconcile real Git revision and clean-workspace checks;
- restore/reconcile actual bounded process execution, timeout, stdout/stderr,
  diff/changed-file capture, and evidence persistence;
- restore/reconcile governance, qualification, verifier, and independent
  acceptance boundaries required by the current product contract;
- ensure current TypeScript/frontend surfaces call or represent real core
  behavior rather than simulated success;
- remove simulated changed-files/verifier PASS from any authoritative execution
  path;
- retain executor PATH detection only as `AVAILABLE`;
- require explicit qualification evidence before an external executor becomes
  `QUALIFIED`;
- audit mini-SWE-agent and any newer executor/API work against the reconciled
  qualification/preflight boundary while preserving useful working integration;
- do not remove working provider/API/authentication plumbing merely because it
  was introduced after the deviation;
- do not introduce routing, fallback, or executor selection as part of this
  repair.

### R4 gate

Mark `DONE` only when:

- one real authorized vertical can execute against a disposable repository;
- execution, timeout, failure, environment-unavailable, and verification states
  remain distinct;
- changed-file scope is checked from observed repository state;
- verifier evidence is real and persisted;
- no authoritative path contains simulated PASS;
- `AVAILABLE != QUALIFIED` is enforced;
- no silent fallback or executor switch is possible.

**Evidence / decision record:** pending.

---

## R5 â€” Full requalification and reconciliation closure

**Status: NOT_STARTED**

Purpose: prove the composed repository, then resume the normal CodePro roadmap.

Perform as one closure tranche:

- run the restored/reconciled regression suite;
- run TypeScript/frontend typecheck/build where still part of the product;
- run package/CLI/foundation checks;
- run the reconciled telemetry/evidence checks;
- run one controlled operational vertical;
- retain the completed llama.cpp Windows runtime qualification as its own
  evidence and run only the minimum smoke necessary to verify integration;
- compare the reconciliation branch against current `main` before merge;
- verify that useful current work is preserved and previously proven critical
  capability is not silently lost;
- reconcile documentation and CI with the actual final architecture;
- merge through a reviewed PR; do not force-push or rewrite published
  `main` history;
- update the canonical `roadmap.md` execution pointer only after this gate.

### R5 gate

Mark `DONE` only when:

```text
NO_LOST_PROVEN_CAPABILITY
AND
NO_UNJUSTIFIED_DUPLICATE_BOUNDARY
AND
NEW_USEFUL_WORK_PRESERVED
AND
OLD_CRITICAL_TESTS_REQUALIFIED
AND
CURRENT_TESTS_PASS
AND
REAL_EXECUTION_PATH_VERIFIED
AND
MAIN_HISTORY_PRESERVED
```

At that point:

```text
RECONCILIATION = DONE
NORMAL_ROADMAP = RESUME
```

**Evidence / decision record:** pending.

---

## Current execution pointer

```text
RECONCILIATION = ACTIVE
CURRENT_BLOCK  = R3
R1             = DONE
R2             = DONE
R3             = IN_PROGRESS
R4             = NOT_STARTED
R5             = NOT_STARTED

NORMAL PHASE 3+ IMPLEMENTATION = PAUSED_BY_RECONCILIATION
```

Completed Phase 0-2 evidence is not invalidated by this pause. Any conflict
found during reconciliation must be recorded rather than silently rewriting a
previous result.

