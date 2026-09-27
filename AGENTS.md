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
