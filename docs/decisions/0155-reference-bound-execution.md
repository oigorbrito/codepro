# Decision 0155 — Reference-bound execution

Date: 2026-09-25

## Result

CodePro adopts a fail-closed reference rule for execution-changing work:

~~~text
NO_REFERENCE -> NO_EXECUTION
~~~

Any task that may implement, modify, invoke, promote, or release execution
behavior must identify the execution/reference profile it is following before
the executor is allowed to act.

Missing, unresolved, mutable-without-disclosure, or scope-incompatible
references produce:

~~~text
BLOCKED_REFERENCE_REQUIRED
~~~

This is a governance decision. It does not authorize a particular executor,
P8.2 publication, release, benchmark claim, or promotion.

## Observed need

CodePro already freezes treatment-affecting identity such as executor/model,
prompt reference and hash, tool-surface reference and hash, parameters,
timeouts, fallback policy, environment, and evidence. The remaining risk is
procedural: an agent can receive a new prompt and begin implementing an
execution approach before identifying which accepted internal contract or
externally demonstrated implementation it is following.

That would allow architectural invention to precede provenance.

The operational release should instead adopt an externally documented,
high-performing execution shape where appropriate and keep CodePro-specific
work concentrated in authority, scope, provenance, verification, replay,
acceptance, and promotion.

## Reference Envelope

Before execution-changing work starts, the task must resolve:

~~~text
reference_profile_ref
reference_profile_revision
reference_evidence_ref
scope_ref
~~~

Meanings:

- reference_profile_ref: internal decision/specification or external
  implementation/configuration being followed;
- reference_profile_revision: immutable commit, version, digest, or an
  explicit statement that the upstream does not expose one;
- reference_evidence_ref: documentation, benchmark/evaluation record, or
  accepted evidence supporting use of that profile;
- scope_ref: CodePro authority/decision defining what may be changed or run.

Additional prompt, tool-surface, executor, adapter, environment, repository,
and revision identities remain governed by their existing CodePro contracts.

A natural-language mention such as "use mini-SWE-agent" or "use Codex" is not
sufficient identity when a concrete version/configuration can be pinned.

## Allowed behavior when the reference is missing

The agent may:

- inspect the repository;
- locate candidate references;
- report that execution is blocked;
- explain what reference is missing.

The agent must not:

- invent or infer an authority reference;
- silently choose a different executor or version;
- implement a new reasoning/planning loop as a substitute;
- silently widen permissions or task scope;
- convert local tests into upstream/benchmark evidence;
- execute the requested operational change before the reference is resolved.

## External-methodology support

This CodePro rule is intentionally stronger than any single external standard.
No external specification found requires literally that every coding-agent
prompt cite a benchmark. The rule is a CodePro synthesis of several established
fail-closed and provenance practices.

### Codex / AGENTS.md

Current Codex documentation states that repository AGENTS.md files are
automatically discovered and injected into the agent context, with more local
instructions overriding broader ones. OpenAI also documents use of AGENTS.md
to make repository workflows mandatory before code changes.

References:

- https://openai.com/index/unrolling-the-codex-agent-loop/
- https://developers.openai.com/api/docs/guides/latest-model
- https://developers.openai.com/blog/skills-agents-sdk

Therefore a short root AGENTS.md is an appropriate enforcement point for
stable repository-wide rules, while detailed rationale remains in versioned
project documentation.

### SLSA provenance

SLSA Build Provenance v1.2 requires a buildDefinition and records externally
controlled parameters and resolved dependencies. It states that the build
definition should contain the information necessary and sufficient to
initialize execution, and at higher assurance levels external parameters must
be complete.

Reference:

- https://slsa.dev/spec/v1.2/build-provenance

Mapping to CodePro:

~~~text
Reference Envelope
    ~ execution definition + resolved identity
Run/event evidence
    ~ run details + provenance
~~~

CodePro applies the same provenance principle before agent execution rather
than only at package build time.

### in-toto

in-toto models a supply chain as explicitly defined steps performed by
authorized functionaries, records commands/materials/products, and provides
artifact rules for what a step may create, modify, or delete. Its guidance
recommends closing most step definitions with DISALLOW * so anything not
explicitly allowed is rejected.

Reference:

- https://in-toto.io/docs/getting-started/

Mapping to CodePro:

~~~text
authorized step + materials/rules
    ~ authorized execution profile + scope/reference envelope

DISALLOW *
    ~ NO_REFERENCE -> NO_EXECUTION
~~~

The concepts are analogous, not identical: CodePro is applying supply-chain
fail-closed semantics to agent execution authority.

### MCP authorization boundary

MCP authorization guidance enforces authorization at the protected-resource
boundary; protected tool calls without valid authorization are rejected before
the tool executes.

Reference:

- https://apps.extensions.modelcontextprotocol.io/api/documents/authorization.html

CodePro keeps the same principle: a missing execution reference is not a
warning to be repaired after execution; it is a pre-execution blocking state.

## Reference execution adoption

For the first operational release, CodePro should avoid inventing a new agent
loop merely to reproduce behavior already demonstrated by an externally
documented implementation.

The intended layering is:

~~~text
CodePro authority / scope / budget
            |
            v
frozen reference execution profile
            |
            v
raw trajectory / patch / execution evidence
            |
            v
CodePro verification
            |
            v
event log / replay
            |
            v
independent acceptance
            |
            v
explicit promotion
~~~

An external benchmark result supports selection of a reference profile; it
does not become CodePro-local acceptance, promotion, or release evidence by
itself.

## Relationship to existing CodePro contracts

This decision strengthens rather than replaces:

- Treatment Configuration Manifest v1;
- qualification-before-executor-binding;
- governance-before-routed-execution;
- independent acceptance;
- promotion-requires-acceptance;
- run provenance and event-log evidence;
- no-silent-fallback / no-silent-executor-switch / no-silent-scope-expansion.

In particular:

~~~text
REFERENCE_PRESENT != QUALIFIED
QUALIFIED != EXECUTED
EXECUTED != VERIFIED
VERIFIED != ACCEPTED
ACCEPTED != PROMOTED
~~~

The reference gate answers only: "is there an explicit, reviewable basis for
the requested execution behavior?" Later gates retain their existing meanings.

## Release consequence

The operational-release critical path becomes:

~~~text
REFERENCE PROFILE FREEZE
        ->
THIN CODEPRO INTEGRATION
        ->
PUBLIC VERTICAL (codepro run)
        ->
EXACT-SHA CI / PACKAGE / PROVENANCE
        ->
INDEPENDENT ACCEPTANCE
        ->
EXPLICIT PROMOTION
~~~

Benchmark exploration, multi-agent architecture, new planners/tool frameworks,
executor ranking, P8.2 optimization, and namespace migration remain outside
this critical path unless separately authorized.
