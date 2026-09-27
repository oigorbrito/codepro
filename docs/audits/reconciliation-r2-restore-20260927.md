# Reconciliation R2 restore evidence — 2026-09-27

**Status:** IN_PROGRESS / VERIFICATION_BLOCKED_INFRA

## Branch

```text
branch = reconcile/04a-capability-recovery
base = 075b6f944ff7c4245139f6f0845ac2db45f31d42
restore_commit = 382c05d350755ba73e05fa7e3a40d4c5af128e2f
source_predecessor = cc44d80a06f2967d3d6e7030409a692921dd6b0a
```

## Restored compatibility substrate

The restore commit is additive only:

```text
122 files restored
  pyproject.toml                          1
  src/arkx/**                            51
  tests/**                               47
  tools/*.py                             21
  mini-SWE provider-free substrate        2
```

No file in the restore commit was deleted or modified relative to the R2 branch
base; the recovered files were added from the exact predecessor blobs.

## Preservation verification

The following useful post-deviation assets have identical blob SHAs before and
after the restore:

```text
server.ts
src/App.tsx
package.json
tsconfig.json
src/chassis/vertical.ts
src/chassis/executionTelemetry.ts
AGENTS.md
roadmap.md
docs/reconciliation-roadmap.md
```

Therefore the R2 restore did not overwrite the current frontend, Express API,
Node/TypeScript package boundary, TS chassis, reconciliation controls, or local
inference telemetry work.

Executor/API qualification branches identified in R1 were not merged or
modified by R2.

## GitHub Actions observation

Push of the restore commit triggered:

```text
Foundation
  run_id = 36329642493
  job runner_id = 0
  steps = []
  conclusion = failure

Mini v2.4.6 provider-free qualification
  run_id = 36329642566
  job runner_id = 0
  steps = []
  conclusion = failure
```

No workflow step executed. This is classified as infrastructure failure and
cannot be used as implementation pass or failure evidence.

```text
INFRA_FAILURE != IMPLEMENTATION_FAILURE
```

## R2 gate state

```text
ADDITIVE_RESTORE = PASS
CURRENT_FRONT_API_PRESERVED = PASS
CURRENT_TS_CHASSIS_PRESERVED = PASS
EXECUTOR_API_BRANCHES_PRESERVED = PASS
PYTHON_PACKAGE_TESTS = NOT_EXECUTED / BLOCKED_INFRA
FOUNDATION_CHECKS = NOT_EXECUTED / BLOCKED_INFRA
TYPESCRIPT_TYPECHECK_BUILD = NOT_EXECUTED / BLOCKED_INFRA

R2 = IN_PROGRESS
```

R2 must not be marked DONE until the restored Python checks and current
TypeScript checks execute successfully in a clean environment.

## Local clean-checkout verification

Validation was executed from a fresh checkout at:

    D:\projetos\codepro-r2-validation

Observed results:

    PythonInstall = PASS
    CliVersion    = PASS
    CliDoctor     = PASS
    CliInspect    = PASS
    Foundation    = PASS
    Baseline      = PASS
    PythonTests   = PASS
    Fingerprint   = PASS
    Compile       = PASS
    NodeInstall   = PASS
    Typecheck     = PASS
    TelemetryTS   = PASS
    FrontBuild    = PASS

The restored mutation probe executed seven known-bad mutations and all seven
were killed. It then aborted before executing the
\spine-ignore-request-scope\ mutation because its configured source anchor
does not exist in the restored \src/arkx/spine.py\.

Both \	ools/mutation_probe.py\ and \src/arkx/spine.py\ were restored from
the same exact predecessor:

    cc44d80a06f2967d3d6e7030409a692921dd6b0a

Therefore this mismatch is classified as:

    MUTATION_PROBE = KNOWN_STALE_VALIDATION_PROBE
    MUTANT_SURVIVED = FALSE
    RECONCILIATION_REGRESSION = FALSE
    R2_BLOCKING = FALSE

The stale mutation anchor is retained as an explicit maintenance issue rather
than being silently reported as PASS.

## Final R2 gate

    ADDITIVE_RESTORE = PASS
    PYTHON_PACKAGE = PASS
    CLI = PASS
    FOUNDATION = PASS
    BASELINE = PASS
    PYTHON_TEST_SUITE = PASS
    PYTHON_COMPILE = PASS
    NODE_INSTALL = PASS
    TYPESCRIPT_TYPECHECK = PASS
    LOCAL_INFERENCE_TELEMETRY_CHECK = PASS
    FRONTEND_BUILD = PASS
    CURRENT_FRONT_API_PRESERVED = PASS
    CURRENT_TS_CHASSIS_PRESERVED = PASS
    EXECUTOR_API_BRANCHES_PRESERVED = PASS
    MUTATION_PROBE = KNOWN_STALE_VALIDATION_PROBE_NON_BLOCKING

    R2 = DONE
    NEXT_BLOCK = R3

