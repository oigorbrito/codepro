# Decision 0155 — Reference-bound execution

Date: 2026-09-25

## Result

CodePro adopts a fail-closed reference rule for execution-changing work:

```text
NO_REFERENCE -> NO_EXECUTION
```

Any task that may implement, modify, invoke, promote, or release execution
behavior must identify the execution/reference profile it is following before
the executor is allowed to act.

Missing, unresolved, mutable-without-disclosure, or scope-incompatible
references produce `BLOCKED_REFERENCE_REQUIRED`.

This is a governance/documentation decision. It does not authorize a
particular executor, P8.2 publication, benchmark claim, release, or promotion.

## Reference Envelope

Before execution-changing work starts, resolve:

```text
reference_profile_ref
reference_profile_revision
reference_evidence_ref
scope_ref
```

- `reference_profile_ref`: internal decision/specification or external
  implementation/configuration being followed.
- `reference_profile_revision`: immutable commit, version, digest, or explicit
  disclosure that the upstream does not expose one.
- `reference_evidence_ref`: documentation, benchmark/evaluation record, or
  accepted evidence supporting use of that profile.
- `scope_ref`: CodePro authority/decision defining what may be changed or run.

A natural-language mention such as "use mini-SWE-agent" or "use Codex" is
not sufficient identity when a concrete version/configuration can be pinned.

## Why this fits existing CodePro contracts

CodePro already freezes executor/model identity, prompt reference and hash,
tool-surface reference and hash, parameters, timeouts, fallback policy,
environment, and evidence. This decision makes the provenance requirement
procedural: the basis must be identified before execution-changing work starts.

## External-methodology support

No external standard reviewed requires literally that every coding-agent
prompt cite a benchmark. `NO_REFERENCE -> NO_EXECUTION` is a CodePro synthesis
of established fail-closed, authorization, and provenance practices.

### Codex / AGENTS.md

Codex documents repository `AGENTS.md` files as instructions discovered and
applied in agent context. This makes a root `AGENTS.md` an appropriate place
for stable repository-wide execution rules.

References:

- https://openai.com/index/unrolling-the-codex-agent-loop/
- https://developers.openai.com/api/docs/guides/latest-model

### SLSA provenance

SLSA Build Provenance v1.2 records a `buildDefinition`, external parameters,
and resolved dependencies, with the goal that execution inputs are complete
and reviewable.

Reference:

- https://slsa.dev/spec/v1.2/build-provenance

CodePro applies the same provenance principle before agent execution rather
than only at package-build time.

### in-toto

in-toto defines authorized steps, functionaries, materials/products, and
artifact rules. Its fail-closed style, including closing rules with
`DISALLOW *`, supports the same design direction: anything outside the
declared execution contract is rejected rather than silently accepted.

Reference:

- https://in-toto.io/docs/getting-started/

### MCP authorization boundary

MCP authorization guidance rejects protected-resource calls that lack valid
authorization before the tool action is performed. CodePro applies the same
pre-execution principle to reference identity.

Reference:

- https://apps.extensions.modelcontextprotocol.io/api/documents/authorization.html

## Reference execution adoption

For the first operational release, CodePro should avoid inventing a new agent
loop merely to reproduce behavior already demonstrated by an externally
documented implementation.

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

External benchmark evidence can justify selecting a reference profile, but it
does not become CodePro-local acceptance, promotion, or release evidence.

## Relationship to existing states

```text
REFERENCE_PRESENT != QUALIFIED
QUALIFIED != EXECUTED
EXECUTED != VERIFIED
VERIFIED != ACCEPTED
ACCEPTED != PROMOTED
```

The reference gate answers only whether an explicit, reviewable basis exists
for the requested execution behavior. Later gates keep their existing meaning.

## Release consequence

```text
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
```

Benchmark exploration, multi-agent architecture, new planners/tool frameworks,
executor ranking, P8.2 optimization, and namespace migration remain outside
this critical path unless separately authorized.
