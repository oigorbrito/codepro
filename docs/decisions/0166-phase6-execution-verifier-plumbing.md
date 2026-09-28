# 0166 - Phase 6 execution and verifier plumbing

Status: ACTIVE FOR PHASE 6

## Context

Phase 5 established one explicit CodePro-to-local-runtime HTTP path. The
normal roadmap now requires generic task execution plumbing before real scaffold
compatibility is evaluated.

The reconciled repository already contains a governed execution spine,
bounded shell-free command execution, changed-file and binary patch capture,
and an independent verifier evidence store. Replacing those boundaries would
duplicate authority.

## Decision

Phase 6 extends the existing vertical with only the missing generic mechanics:

```text
exact source revision
-> isolated detached Git worktree
-> explicit inspect/edit/command operations
-> existing governed execution spine
-> observed changed files + binary patch + stdout/stderr
-> existing independent verifier
-> persisted verifier evidence
-> persisted final repository state
-> worktree cleanup
```

The following modules own the new mechanics:

- `arkx.isolated_workspace`: creates/removes an exact detached Git worktree
  and records initial/final repository state.
- `arkx.repository_operations`: explicit repository-local inspect, edit, and
  command primitives for future scaffold adapters.
- `tools/phase6_fixture_scaffold.py`: deterministic controlled scaffold
  fixture used only to prove the plumbing.
- `tools/run_phase6_validation.py`: composes the fixture with
  `arkx.vertical.run_vertical` and persists evidence.

The existing `arkx.vertical.run_vertical`,
`LocalCommandEnvironment`, and `VerificationEvidenceStore` remain
authoritative for execution observation, process semantics, patch capture, and
independent verification.

## Scope boundary

Phase 6 does not qualify a real scaffold and does not select or invoke a model.

```text
CONTROLLED_SCAFFOLD_FIXTURE != QUALIFIED_SCAFFOLD
MODEL_NOT_INVOKED != MODEL_FAILURE
IMPLEMENTED != EXECUTED
EXECUTED != VERIFIED
VERIFIED != ACCEPTED
ACCEPTED != PROMOTED
```

The model/runtime transport was proven separately in Phase 5. Phase 7 owns the
first compatibility runs that connect each real scaffold candidate to that
local runtime. This prevents Phase 6 from pre-selecting a scaffold or silently
collapsing scaffold compatibility into generic execution plumbing.

## Gate

A controlled Phase 6 pass requires all of the following:

- isolated clean worktree at an exact recorded revision;
- source repository remains unchanged;
- observed INSPECT, EDIT, and COMMAND operations;
- changed-file and patch evidence;
- executor stdout/stderr evidence;
- command/test evidence;
- independent verifier PASS with separately persisted raw evidence;
- persisted final repository state;
- execution/verifier duration telemetry;
- successful worktree cleanup.

A fixture pass is local plumbing evidence only. It is not scaffold
qualification, model performance evidence, acceptance, or promotion.

## Rejected alternatives

- New orchestration system: rejected because the governed vertical already
  provides the required execution authority.
- Reusing the source checkout directly: rejected because Phase 6 explicitly
  requires isolated task workspace behavior.
- Treating the executor command as the verifier: rejected because verification
  must remain independent.
- Invoking one real scaffold/model in Phase 6: rejected because that would
  pre-empt the frozen Phase 7 compatibility pool.

## Removal / extension condition

Remove either new boundary if a later qualified scaffold supplies the same
behavior through the authoritative CodePro contracts without losing exact
revision identity, isolation, scope checks, independent verification, evidence,
or cleanup semantics.
