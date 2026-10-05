# Decision 0170 — CodePro canonical Python namespace migration

## Status

Accepted for staged implementation; the namespace facade and packaging slice
are implemented locally but not released.

## Decision

`codepro` is the canonical product and Python package namespace. `arkx` is
retained temporarily as a compatibility shim and must not be treated as a
separate product identity.

The migration is staged:

1. implement the canonical package under `codepro`;
2. update internal imports, CLI entry points, packaging metadata, and current
   documentation to use `codepro`;
3. retain `arkx` re-exports for the declared compatibility window;
4. test equivalence of the supported public API through both namespaces;
5. deprecate and remove `arkx` only in a separately authorized release.

No implementation or evidence is promoted merely because this decision exists.

## Rationale

The product identity is CodePro, while the current Python namespace is `arkx`.
An atomic rename would break imports, dynamic module references, serialized
objects, manifests, historical evidence, and external scripts without proving
that all consumers had migrated. A compatibility shim preserves continuity
while making the intended namespace explicit.

## Acceptance criteria

- `import codepro` exposes the canonical public API;
- `codepro.__all__` is explicit and tested;
- supported `arkx` imports resolve to the corresponding `codepro` objects;
- `codepro` and `arkx` do not silently expose different behavior;
- the CLI and wheel identify the distribution as `codepro`;
- no claim of completed migration is made until installed-package and source
  import tests pass at the same revision;
- removal of the `arkx` shim requires a later decision and release boundary.

## Non-goals

- no redesign of the execution chassis;
- no provider, model, executor, or benchmark qualification;
- no deletion of historical `arkx` evidence;
- no automatic removal of legacy imports.

## Current evidence

The current checkout still has `arkx` as the implementation namespace, while
`codepro` now provides the canonical facade and packaging entry point. The
installed-package and full compatibility gates remain open until a wheel is
built and tested in a clean environment.
