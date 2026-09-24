# Codepro agent operating rules

The product identity is Codepro. `arkx` is the current Python namespace and
must not be treated as a separate product identity.

## Scope

Treat this repository as an evidence-oriented software-engineering project.
The presence of a module, adapter, test, or document does not prove that the
corresponding capability is qualified for adoption.

## Required implementation standard

Every material capability change must have:

1. an explicit contract or decision record;
2. a falsifiable hypothesis and empirical acceptance criteria;
3. executable tests for deterministic behavior and failure boundaries;
4. recorded raw evidence, including environment and identity where relevant;
5. an independent acceptance decision before promotion.

Local unit-test success is local evidence only. It must not be reported as
upstream, scientific, benchmark, or provider evidence.

## Harness rules

- Preserve provider, model, version, configuration, budget, runtime, and
  treatment identity in every execution record.
- Use stable run identity for equivalent frozen inputs.
- Execute serially when the experiment requires controlled comparison.
- Never silently overwrite an attempt directory or select a fallback executor.
- Persist execution artifacts atomically and keep execution, verification,
  acceptance, and promotion as separate states.
- Represent missing identity, missing evidence, blocked infrastructure, and
  indeterminate outcomes explicitly; none may become success by inference.
- A failure must retain enough raw output and environment facts to support
  diagnosis and reproducibility.

## Routing and promotion

Route the request before selecting an executor. Simple, localized, and
repository-wide paths are treatment regimes, not implicit executor cascades.
Fallbacks, executor switches, scope expansion, acceptance, and promotion must
be explicit and evidence-backed.

Do not promote a provider, model, executor, or treatment until the declared
authority has accepted the required evidence. A Gold or infrastructure
qualification validates its stated authority and does not by itself prove
mechanism effectiveness or general model quality.

## Change discipline

- Preserve unrelated working-tree changes.
- Prefer the smallest change that satisfies the contract.
- Add or update tests with behavioral changes.
- Update the relevant architecture, protocol, or decision documentation when
  the boundary changes.
- Run the focused tests first, then the complete test suite when practical.
- Do not claim merge readiness while required evidence or acceptance records
  are still missing.

## Current baseline

The recorded external authority result is `resolved: true` for the official
SWE-bench Docker Gold path on the frozen tasks under `logs/evaluation/`. This
does not qualify a real provider/model or the A/B/C/D mechanism trial.
