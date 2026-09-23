# ADR 0022 — Rename public product identity to CodePro

## Status

Accepted.

## Context

The project identity changed from the short-lived Dekon name to CodePro after the first installable CLI boundary had already been merged.

The rename affects public product identity, packaging metadata, console command, current documentation, and CI probes. It does not by itself justify changing stable internal schemas or the Python implementation namespace.

## Decision

Use **CodePro** as the canonical project and product name.

The public CLI contract becomes:

- package distribution name: `codepro`;
- console command: `codepro`;
- version output: `codepro <version>`;
- current documentation and product-boundary language: CodePro.

The Python implementation namespace remains `arkx` temporarily. Existing schema fields and provenance identities that embed `arkx` are not renamed in this ADR because doing so would be a schema migration that changes frozen identities and empirical fixtures.

No `dekon` console alias is retained because the name was not promoted as a compatibility commitment.

## Empirical acceptance

The rename is accepted only if:

1. editable installation succeeds as `codepro`;
2. `codepro --help`, `codepro --version`, and `codepro doctor` pass;
3. no `dekon` console script is declared;
4. the complete test suite remains green on Python 3.12, 3.13, and 3.14;
5. the canonical chassis semantic fingerprint remains unchanged;
6. mutation sensitivity remains unchanged.

## Boundary

This ADR is a product-identity rename only. A future `arkx` namespace/schema migration requires a separate decision, compatibility plan, and fixture/hash migration strategy.
