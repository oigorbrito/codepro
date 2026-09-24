# ADR 0013 — Version the empirical execution environment

## Status

Accepted for the Arkx empirical chassis.

## Observed need

The CI already pins Python and the runner family and prints a small fingerprint. A raw log alone is not a durable schema for comparing environment facts across runs, and the hosted runner still contains residual drift.

## Decision

Add Environment Manifest v1 and pin external GitHub Actions by full commit SHA.

The manifest records OS/version, runner image/version, architecture, Python implementation/version, locale, timezone, dependency-lock state, container state, external action pins, network policy, and whether the environment is actually hermetic.

When the environment is non-hermetic, residual drift must be declared rather than hidden.

## Alternatives considered

- Claim the hosted runner is reproducible because its label is pinned: rejected; the label selects a moving managed image.
- Introduce a container solely for foundation tests: deferred because the current standard-library chassis does not yet justify the added layer.
- Keep action tags such as `@v4`: rejected for empirical CI because tags are less immutable than full commit SHAs.

## Limitation

Recording the hosted runner image version improves auditability but does not provide bit-for-bit reconstruction. Stronger hermeticity can be introduced later if experiments demonstrate that environment drift materially affects results.

## Rollback/removal condition

Replace this contract if execution moves to a stronger immutable environment representation that captures the same facts with less duplication.
