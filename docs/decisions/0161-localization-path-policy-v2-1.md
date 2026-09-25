# Decision 0161: Localization path policy V2.1

Status: accepted for implementation on the stacked C1 localization line.

This decision extends `C1_REPOSITORY_RELATIVE_PATH_V2` without changing its
lexical, filesystem-free boundary.

## Contract

- `candidate_files` represents concrete files, not directory identifiers.
- A non-empty path whose normalized representation ends in `/` is rejected.
  This applies equally to an input ending in `\\` after separator
  normalization.
- A non-drive colon is preserved as a POSIX lexical identity, so `foo:bar`
  remains valid.
- Drive-relative and absolute Windows paths remain rejected (`C:foo`,
  `C:/foo`, and `C:\\foo`).
- Portability scope remains `POSIX_CANONICAL_ONLY`; this decision does not
  introduce a general Windows reserved-character policy.
- Whitespace semantics remain deferred.

## Non-goals

No filesystem lookup, path resolution, existence check, cwd dependence,
symlink handling, provider/model/runtime invocation, or promotion is introduced.

## Acceptance

Focused tests must prove trailing-separator rejection, non-drive-colon
preservation, drive-path rejection, and continued V2 canonicalization and
semantic deduplication.
