# Decision 0112 — Package boundary and distribution identity

## Status

Proposed for G1 validation; not a product-release acceptance decision.

## Context

The current audit line contains a usable `arkx` Python package but no build
metadata or clean-install contract. The previous G3 CLI implementation belongs
to a different architecture and cannot be promoted by cherry-pick. A package
boundary is therefore required before a public entrypoint or executor can be
evaluated.

## Decision

- The import namespace remains `arkx`.
- The distribution identity is `codepro`, matching the current product name.
- The first packaged version is `0.3.0.dev0`, explicitly non-release.
- The package has no runtime dependencies and requires Python `>=3.12`.
- This decision adds packaging only; it does not add a CLI, provider, model, or
  executor.

## Falsifiable hypothesis and acceptance criteria

H1: A clean Python 3.13 environment can build and install the distribution
without `PYTHONPATH`, import `arkx`, run the existing foundation check and pass
the complete test suite.

Acceptance requires a wheel and sdist, SHA-256 hashes, the exact Python and
package versions, raw command output, and an independent acceptance decision.
Any build, import, or test failure is `NO-GO` for G1.

## Removal condition

Remove or revise this boundary if the public product identity, supported Python
range, or packaging backend changes; do not silently rename the distribution.
