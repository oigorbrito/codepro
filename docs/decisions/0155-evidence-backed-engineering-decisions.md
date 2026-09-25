# Decision 0155 — Evidence-backed engineering decisions

Date: 2026-09-25

## Result

CodePro requires a reviewable basis for non-trivial engineering decisions.

This replaces the earlier, overly broad interpretation
`NO_REFERENCE -> NO_EXECUTION`. CodePro does **not** require every code change
to originate in a benchmark or external study.

The operative rule is:

```text
NON_TRIVIAL_DECISION
    -> IDENTIFY_PROBLEM_CLASS
    -> STATE_DECISION_BASIS
    -> CHECK_REFERENCE_FIT
    -> IMPLEMENT
```

When no suitable external or project reference exists, the decision may still
proceed as an explicit `LOCAL_DESIGN_HYPOTHESIS`. It must not be represented
as established best practice or externally validated design.

## Decision Basis

For a non-trivial change, record:

```text
problem_class
decision
basis_type
basis_ref
supported_claim
applicability
deviation
```

Allowed basis types:

```text
STANDARD
OFFICIAL_DOC
UPSTREAM_IMPL
BENCHMARK
PROJECT_INVARIANT
LOCAL_EVIDENCE
LOCAL_DESIGN_HYPOTHESIS
```

The basis must match the engineering problem.

Examples:

- stacked Git branches -> Git rebase/branch semantics;
- packaging -> PyPA;
- security design -> NIST/OWASP/applicable standard;
- agent execution behavior -> upstream agent implementation/docs;
- performance claims -> relevant benchmark/study;
- CodePro state transitions -> CodePro ADR/spec/invariant;
- deletion of obsolete code -> dependency/use evidence plus applicable design
  principle or upstream migration/removal guidance.

The goal is not citation density. The goal is causal traceability:

```text
REFERENCE_FIT > REFERENCE_COUNT
```

## Structural-change rule

Creating or deleting a module, class, abstraction, adapter, fallback, routing
layer, cache, retry controller, dependency, public command, or persistence
boundary is a design decision.

Before the structural change, the executor must explain:

1. the observed problem;
2. why the chosen structure addresses it;
3. what source or project invariant supports the mechanism;
4. why the source applies to the current CodePro context;
5. what deviation, if any, CodePro is making from that reference.

Assertions such as "cleaner", "more flexible", "future-proof", or "best
practice" are not sufficient without a concrete basis.

## Research-before-workaround stop condition

The project previously encountered a stacked-PR failure mode where a dependency
problem was repeatedly moved into later corrective PRs instead of changing the
stacking method.

CodePro now treats repeated workaround as a stop condition.

If the same underlying problem:

- survives two materially similar attempts;
- is moved into another module, layer, branch, or PR;
- produces successive corrective PRs without changing the root mechanism; or
- accumulates special cases around the same unresolved constraint,

then:

```text
REPEATED_WORKAROUND
    -> STOP_LOCAL_PATCHING
    -> RESTATE_ROOT_PROBLEM
    -> CLASSIFY_DOMAIN
    -> CONSULT_AUTHORITATIVE_SOURCE
    -> COMPARE_MECHANISM
    -> RESUME_WITH_REFERENCED_APPROACH
```

The threshold is operational, not statistical: two failed or displaced
attempts are enough to require a change in method before a third materially
similar workaround.

### Stacked-branch example

Git's own documentation describes rebasing as replaying a branch's patches on
a new base and documents `git rebase --onto <newbase> <upstream> <branch>`
for moving work from one topic-branch ancestry onto another base.

Reference:

- https://git-scm.com/book/en/v2/Git-Branching-Rebasing
- https://git-scm.com/docs/git-rebase

For a stack such as:

```text
main
└── A
    └── B
        └── C
```

after A is integrated, the engineering question is normally how to transplant
or replay the remaining topic work onto the new base. Creating B', C', D' as
successive corrective layers can preserve the ancestry problem rather than
solve it.

This is an example of why domain documentation should replace repeated local
guessing once the failure mode becomes recurrent.

## External methodology support

### Google engineering practices

Google's public code-review guidance says review should evaluate design,
functionality, complexity, tests, naming, comments, style, and documentation.
Its CL-description guidance specifically requires the author to explain both
what changed and why, including context and decisions not visible in the code.

References:

- https://google.github.io/eng-practices/review/
- https://google.github.io/eng-practices/review/developer/cl-descriptions.html
- https://google.github.io/eng-practices/review/reviewer/looking-for.html

CodePro extends the "why" requirement by asking for a concrete Decision Basis
when the choice is non-trivial.

### NIST SSDF

NIST SP 800-218 SSDF PW.1.2 requires tracking software security requirements,
risks, and design decisions. NIST's accompanying DevSecOps analysis describes
preserving design decisions and their rationale so future analysis can
understand why a mitigation or alternative was chosen.

References:

- https://csrc.nist.gov/pubs/sp/800/218/final
- https://pages.nist.gov/nccoe-devsecops/appendix-c.html

The CodePro rule is broader than the security scope of SSDF, but follows the
same traceability principle: preserve the reason for a consequential design
choice, not just the resulting code.

## Reference quality and claim scope

A source can only support the claim it actually establishes.

Examples:

```text
Git docs
    -> supports Git mechanics
    != supports agent quality

SWE-bench result
    -> supports measured task performance under that setup
    != universal architecture proof

upstream implementation
    -> supports how that implementation behaves
    != proof that CodePro must copy it

CodePro ADR
    -> supports an accepted project constraint
    != external scientific evidence
```

The executor must separate:

```text
SOURCE_FACT
PROJECT_INFERENCE
LOCAL_HYPOTHESIS
```

## Execution-profile adoption

For the first operational release, CodePro should prefer a frozen,
externally documented coding-agent execution profile rather than inventing a
new agent loop without a demonstrated need.

That is one application of this decision, not the definition of the policy.

The intended layering remains:

```text
CodePro authority / scope / budget
            ->
frozen reference execution profile
            ->
raw trajectory / patch / execution evidence
            ->
CodePro verification
            ->
event log / replay
            ->
independent acceptance
            ->
explicit promotion
```

External benchmark evidence may justify choosing a reference profile. It does
not become CodePro-local acceptance, promotion, or release evidence.

## Relationship to existing states

```text
REFERENCE_PRESENT != QUALIFIED
QUALIFIED != EXECUTED
EXECUTED != VERIFIED
VERIFIED != ACCEPTED
ACCEPTED != PROMOTED
```

A Decision Basis answers "why this mechanism?" It does not answer whether the
implementation executed correctly, was independently accepted, or should be
promoted.

## Consequence for agent behavior

The agent should challenge an executor's non-trivial proposal with:

```text
What problem are you solving?
Why this mechanism?
What is the strongest applicable reference?
What exact claim does that reference support?
How does it map to this repository?
What is local invention versus referenced practice?
```

This applies equally to adding code, deleting code, changing structure, and
changing operational procedure.
