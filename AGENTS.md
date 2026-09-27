# CodePro agent policy

This file defines repository-wide instructions for coding agents.

## Evidence-backed engineering decisions

CodePro does not require every line of code to originate in a benchmark or
external study. It requires non-trivial engineering decisions to have an
explicit, reviewable basis.

Before implementing a structural, behavioral, operational, or architectural
decision, the agent must be able to answer:

```text
WHAT is changing?
WHY is this the appropriate mechanism?
WHAT is the basis for that choice?
WHY does that basis apply here?
```

The basis should be the most authoritative source appropriate to the problem,
not a generic citation added after the fact.

Examples:

- Git history / stacked-branch mechanics -> Git documentation;
- Python packaging -> PyPA specifications/guides;
- security controls -> NIST / OWASP / applicable standards;
- external executor behavior -> upstream implementation/docs and benchmark
  evidence when performance claims matter;
- repository-specific invariants -> CodePro ADR/spec/contract;
- removal of a class/module -> dependency/use evidence plus the design rule or
  upstream practice that makes removal preferable;
- algorithm/performance choice -> paper, benchmark, implementation evidence, or
  explicit measured local constraint.

A benchmark is one possible basis. It is not the universal basis.

## Decision Basis record

For non-trivial changes, keep a compact Decision Basis in the task reasoning,
change description, or associated decision record:

```text
problem_class = <what kind of engineering problem this is>
decision = <mechanism chosen>
basis_type = <STANDARD | OFFICIAL_DOC | UPSTREAM_IMPL | BENCHMARK |
              PROJECT_INVARIANT | LOCAL_EVIDENCE | LOCAL_DESIGN_HYPOTHESIS>
basis_ref = <specific source, file, ADR, commit, URL, or evidence record>
supported_claim = <what the source actually supports>
applicability = <why it applies to this CodePro change>
deviation = <none, or explicit difference from the reference>
```

Do not cite a source for a claim it does not support.

```text
REFERENCE_FIT > REFERENCE_COUNT
```

## Local hypotheses are allowed

If no suitable external or project reference exists, implementation is not
automatically forbidden.

The executor must instead classify the choice explicitly:

```text
basis_type = LOCAL_DESIGN_HYPOTHESIS
```

and state the assumptions, expected consequence, and rollback/removal
condition. It must not present the choice as an established best practice,
benchmark-proven design, or upstream requirement.

Routine mechanical edits, direct bug fixes with an already-established cause,
formatting, and changes whose mechanism is fully determined by an existing
CodePro contract do not require external research.

## Research-before-workaround rule

Repeated workaround is a stop condition.

If the same underlying problem:

- survives two implementation attempts;
- is displaced into another module, layer, branch, or pull request;
- causes successive corrective PRs without resolving the root condition; or
- requires increasingly special-case behavior,

then the next step is not another workaround.

```text
REPEATED_WORKAROUND -> ROOT_CAUSE_REFRAME -> AUTHORITATIVE_RESEARCH
```

Before a third materially similar attempt, the agent must:

1. restate the root problem independently of the current patch;
2. classify the problem domain;
3. consult the authoritative source for that domain;
4. compare the documented mechanism with the current approach;
5. change the implementation strategy if the reference contradicts it.

Example: for stacked Git branches, consult Git's rebase/--onto semantics rather
than creating successive corrective branches that preserve the same ancestry
problem.

## Structural changes need a basis

Adding or deleting a module, class, abstraction, adapter, fallback, routing
layer, cache, retry controller, dependency, public command, or persistence
boundary is a design decision.

The executor must identify the basis before making the structural change.
"Cleaner", "more flexible", "future-proof", and "best practice" are not
sufficient by themselves.

Prefer removal or reuse when the reference and current code show that a new
abstraction is unnecessary.

## Execution-profile adoption

For the first operational release, prefer a frozen, externally documented
coding-agent execution profile over inventing a new CodePro-specific reasoning,
planning, tool-selection, or multi-agent loop.

CodePro owns request/authority, scope/budget, exact profile binding,
environment/revision identity, trajectory/artifact capture, verification,
event log/replay, independent acceptance, and explicit promotion.

The adopted executor owns task-solving behavior inside the frozen profile.
Do not reimplement its reasoning loop unless a separate decision explicitly
justifies that work.

## Roadmap synchronization is mandatory

`roadmap.md` is the canonical living execution plan for CodePro.

Whenever an implementation or qualification item is completed and verified,
the executor must update `roadmap.md` in the same change or immediately
afterward and mark the corresponding item complete.

```text
IMPLEMENT
-> TEST
-> CAPTURE EVIDENCE
-> VERIFY
-> MARK COMPLETE IN roadmap.md
```

Writing code alone does not satisfy this rule.

```text
IMPLEMENTED != COMPLETE
EXECUTED != VERIFIED
```

The executor must:

1. identify the roadmap item that authorizes or tracks the work;
2. implement or execute the qualification step;
3. capture the evidence required by that roadmap gate;
4. change the item to `[x]` only after verification succeeds;
5. update phase status and the current execution pointer when applicable;
6. add or revise roadmap items when scope legitimately changes instead of
   silently expanding scope.

If verification fails, leave the item incomplete and record `[!]` BLOCKED or
`[~]` IN_PROGRESS as applicable.

Deleting or bypassing `roadmap.md`, or removing this rule from `AGENTS.md`,
requires an explicit superseding decision. Incidental scaffolding, cleanup, or
refactoring must not remove either control.


## Active reconciliation control

When `docs/reconciliation-roadmap.md` exists with `Status: ACTIVE`, it is a
mandatory execution control for repository-recovery work.

Before making any reconciliation, restoration, migration, executor-boundary,
telemetry-boundary, or architecture-repair change, the agent must read:

```text
docs/reconciliation-roadmap.md
```

The reconciliation roadmap temporarily controls the execution order for the
repair while `roadmap.md` remains the canonical project roadmap.

The agent must:

1. identify the active reconciliation block before editing;
2. work the block as one coherent tranche rather than fragmenting it into
   unnecessary micro-patches;
3. remain inside that block's declared scope;
4. capture the block's required evidence;
5. mark the block `DONE` only after its gate passes;
6. update the block's evidence/decision record when status changes;
7. update `roadmap.md` when the reconciliation pointer or normal project
   pointer changes;
8. stop and mark `BLOCKED` rather than inventing a workaround when the gate
   cannot be established;
9. not begin the next implementation block until the current block is
   `DONE`, except for read-only evidence collection needed to remove a block;
10. not use blind whole-tree revert, force-push, published-history rewrite, or
    silent architectural replacement.

The required repair decision vocabulary is:

```text
KEEP     = useful current capability remains
RESTORE  = previously proven capability returns
MERGE    = old and new useful behavior are reconciled
DROP     = duplication/regression removed with explicit evidence
```

A newer implementation has no automatic priority over a previously validated
one, and historical validation does not automatically validate restored code.

```text
NEWER != BETTER
OLD_PASS != RECONCILED_PASS
RESTORE != BLIND_REVERT
```

When all reconciliation blocks are `DONE`, the agent must mark the
reconciliation roadmap inactive/complete and resume the normal execution
pointer in `roadmap.md`.

## Existing state separation remains normative

```text
SAME_NAME != SAME_TREATMENT
LOCAL_PASS != UPSTREAM_EVIDENCE
REFERENCE_PRESENT != QUALIFIED
QUALIFIED != EXECUTED
EXECUTED != VERIFIED
VERIFIED != ACCEPTED
ACCEPTED != PROMOTED
NO_SILENT_FALLBACK
NO_SILENT_EXECUTOR_SWITCH
NO_SILENT_SCOPE_EXPANSION
```

Detailed rationale and external-methodology mapping:
`docs/decisions/0155-evidence-backed-engineering-decisions.md`.

This policy does not authorize an executor, P8.2 publication, release, or
promotion. Those remain separate decisions with their own evidence and
acceptance records.
