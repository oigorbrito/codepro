# Reconciliation R1 audit — 2026-09-27

**Status:** DONE  
**Scope:** read-only capability inventory and recovery-boundary definition  
**Production code restored:** no

## Exact identities

```text
AUDIT_START_MAIN = ea92db4e070ff096820d40df710aa9df81770a7e
DEVIATION_COMMIT = 04a670e40f5d4ee7eb93a554a745a0bf3cbde8d7
RECOVERY_PREDECESSOR = cc44d80a06f2967d3d6e7030409a692921dd6b0a
```

The deviation commit is the direct child of the recovery predecessor and changed
approximately:

```text
+3,099 lines
-25,289 lines
```

The predecessor tree contained 242 tracked blobs. The audited current main
contained 145 tracked blobs.

## Preservation sources outside current main

The reconciliation must also preserve executor/API qualification work that is
present on remote branches but not on current `main`.

```text
ops/gemini-cli-executor-qualification
  head = e9212f3c8ff4323e81fbeeaac09c8731359c5789

ops/mini-v246-executor-qualification
  head = dabbc2dc8dcd835ce5521bb9e9eed60aec48c68b

ops/mini-v246-gemini-api-qualification
  head = 89449861c6839d48ffdbbe5c0b485b15db3b1ed7

ops/mini-v246-runtime-access
  head = c43c8a5a622d5ddeb9e61fd570d83d5d54e17b53

ops/mini-v246-runtime-access-split
  head = 6e354cc02a722e5665bd640e24d1834a4dbd8bfd

ops/mini-v246-verifier-controls-split
  head = 0bde4a2125809ad914a9bb3a178ff468261be6b5
```

Observed branch-only assets include:

- Gemini CLI executor qualification runner/tests;
- mini-SWE-agent v2.4.6 executor qualification runner/tests;
- mini-SWE-agent + Gemini API qualification runner/tests;
- runtime-access and verifier-control runners/tests/workflow;
- preserved runtime/verifier evidence on split evidence branches.

The Gemini API qualification runner explicitly uses:

```text
model = gemini/gemini-2.5-flash
credential = GEMINI_API_KEY
executor = mini-swe-agent v2.4.6
environment = docker
official verifier = SWE-bench 5.0.2
fallback = forbidden
promotion = NOT_AUTHORIZED
```

The Gemini CLI qualification runner is distinct: it expects an already
authenticated Gemini CLI account and explicitly does not use a Gemini API key.

These branches are preservation sources. They are not automatically promoted
into the reconciled product.

## Current-main provider/API observation

Current tracked `main` contains the Express HTTP API and React frontend, but
code search found no concrete provider credential/client binding in current
main for `API_KEY`, OpenAI, or xAI. Gemini references on main are principally
inspection/documentation rather than a provider client.

Therefore:

```text
NO_PROVIDER_CLIENT_ON_CURRENT_MAIN
!=
NO_PROVIDER_API_WORK_EXISTS
```

The remote ops branches above are explicit evidence that executor/provider/API
qualification work exists and must not be lost. Local or unpushed work remains
outside this GitHub-only audit and must be preserved separately if present.

## Capability reconciliation matrix

| Capability | Predecessor state | Current/other state | R1 disposition | Reason / next block |
| --- | --- | --- | --- | --- |
| Python package boundary / `pyproject.toml` | present, installable `codepro` | removed; Node package added | **RESTORE + KEEP** | restore Python compatibility package while keeping Node package; R2 |
| Python `src/arkx/**` operational core | present as coherent package | completely absent from main | **RESTORE** | restore exact compatibility substrate before semantic merge; R2 |
| Python CLI `codepro` / `python -m arkx` | implemented + tested | docs/CI still expect it; code absent | **RESTORE** | current repo is internally inconsistent without it; R2 |
| Python regression suite | 47 tracked test files | absent | **RESTORE** | test boundary was deleted wholesale; R2 |
| Python validation tools | 21 tracked tools | almost all absent | **RESTORE selectively as validated substrate** | restore predecessor tools required by restored tests/gates; R2 |
| React/Vite/Tailwind frontend | absent | present | **KEEP** | useful post-deviation operator surface; never remove merely to restore Python |
| Express `server.ts` HTTP API | absent | present | **KEEP + MERGE** | preserve transport/API surface; later rebind authoritative endpoints to real core; R4 |
| Node package / TS build config | absent | present | **KEEP** | independent frontend/server build surface; R2 must not remove it |
| TS inspection | absent | present; adds mini-SWE/SWE-agent/OpenHands PATH detection | **KEEP** | observational capability only; `AVAILABLE != QUALIFIED` |
| TS characterization/progress/routing | Python equivalents existed | simplified TS variants present | **MERGE** | preserve current UI/API contracts; determine canonical semantics after foundation recovery |
| Generic telemetry / `ExecutionRecord` | implemented + tested in Python | generic TS event contract + new inference telemetry | **MERGE** | old generic semantics + new local-inference fields; R3 |
| Measurement Contract | implementation + tests | docs/fixture survive; implementation removed | **RESTORE + MERGE** | restore implementation, then bind new local metrics; R3 |
| Run provenance | implementation + tests | docs/fixture survive; implementation removed | **RESTORE + MERGE** | preserve content-addressed provenance; R3 |
| Event log / replay integrity | implementation + tests | normative docs survive; implementation removed | **RESTORE** | no equivalent current implementation observed; R3 |
| TS local-inference telemetry | absent | implemented after Phase 2 measurements | **KEEP + MERGE** | fields are useful; must not become a duplicate generic telemetry system; R3 |
| Real command execution | implemented in Python | TS vertical does not invoke executor command | **RESTORE + MERGE** | retain current API/interface while restoring real execution; R4 |
| Git revision / clean-worktree enforcement | implemented in Python vertical | not enforced by current TS vertical | **RESTORE** | required operational boundary; R4 |
| Changed-file observation | real Git-derived evidence | current TS uses `simulatedChangedFiles` | **MERGE** | preserve interface, replace simulation with observed repository state; R4 |
| Verifier execution/evidence | real command + persisted evidence | current TS records verifier `PASS` without execution | **RESTORE + MERGE** | no authoritative simulated PASS; R4 |
| Governance / qualification | implemented + tested | simplified/missing in current TS core | **RESTORE + MERGE** | required before executor binding; R4 |
| M1 acceptance | implemented evidence-only review | TS evidence-only review also present | **MERGE** | keep useful UI/API review surface, reconcile with proven acceptance semantics; R4 |
| mini-SWE provider-free preflight/harness | present + tests | core files/tests removed; docs/config survive | **RESTORE** | executor qualification dependency; restore substrate R2, qualify/use R4 |
| Gemini CLI qualification work | branch-only | not on main | **KEEP as preservation source / MERGE later** | do not lose auth/executor work; R4 |
| mini-SWE + Gemini API qualification | branch-only | not on main | **KEEP as preservation source / MERGE later** | preserve API/auth/model/verifier work; R4 |
| Runtime/verifier-control qualification work | branch-only | not on main | **KEEP as preservation source / MERGE later** | prerequisite evidence for executor qualification; R4 |
| llama.cpp Windows qualification | absent historically | new Phase 2 evidence | **KEEP** | independent verified runtime evidence; R3/R5 integration only |
| `AGENTS.md`, reconciliation roadmap, current roadmap | old control was removed by deviation then restored/strengthened | current controls active | **KEEP CURRENT** | never restore predecessor copies over current control docs |
| Current docs/fixtures that survived migration | present historically/currently | retained | **KEEP** | no reason to replace identical/surviving evidence |

## DROP disposition

R1 authorizes **no DROP**.

A future DROP requires evidence of regression, duplication, incompatibility, or
supersession with equivalent-or-stronger capability. In particular, no
executor/provider/API branch or frontend/server asset may be dropped merely
because it is not present in the predecessor.

## Historical evidence semantics

Historical passes prove that a capability existed and was exercised on the
historical revision. They do not automatically validate restored code on the
reconciliation branch.

```text
OLD_PASS != RECONCILED_PASS
RESTORED_CODE -> RERUN_REQUIRED_GATES
```

The Phase 2 Windows/llama.cpp evidence is post-deviation independent evidence
and remains preserved.

## Bounded R2 tranche

R2 is intentionally one additive compatibility-restoration block.

Starting from the reconciled branch created from current main:

1. restore `pyproject.toml` from `cc44d80a06f2967d3d6e7030409a692921dd6b0a`;
2. restore the complete `src/arkx/**` package snapshot from that predecessor
   as a compatibility substrate;
3. restore the predecessor `tests/**` regression boundary;
4. restore predecessor Python validation tools required by those tests and
   foundation/release checks;
5. restore the two deleted mini-SWE provider-free substrate files:
   - `experiments/integrations/minisweagent/preflight.py`
   - `experiments/integrations/minisweagent/provider_free_task_harness.py`;
6. do **not** remove or overwrite:
   - `package.json`, `bun.lock`, `tsconfig.json`, `vite.config.ts`;
   - `server.ts`, `index.html`, `src/App.tsx`, `src/main.tsx`,
     `src/index.css`, `src/chassis/**`;
   - current `AGENTS.md`, `roadmap.md`, reconciliation docs;
   - Phase 2 runtime evidence;
7. do not import the ops executor/API branches in R2; preserve their exact heads
   for R4, after the foundational package and test boundary are coherent;
8. rerun the restored Python package/foundation/regression checks and the
   current TypeScript typecheck/build. Failures remain failures/blocks; no
   silent deletion of either stack is permitted.

R2 is a compatibility restoration, not final architecture selection. R3 and R4
own semantic deduplication/rebinding.

## R1 gate result

```text
EXACT_IDENTITIES_RECORDED = PASS
CRITICAL_CAPABILITY_MATRIX = PASS
EXECUTOR_API_BRANCHES_INVENTORIED = PASS
COLLISIONS_DISPOSITIONED = PASS
DROP_AUTHORIZED = NONE
NEXT_TRANCHE_BOUNDED = PASS

R1 = DONE
```
