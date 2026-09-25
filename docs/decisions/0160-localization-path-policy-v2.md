# Decision 0160: C1 repository-relative path policy v2

## Status

Validated as a stacked follow-up to PR45. Promotion is not authorized.

## Policy

Localization candidate files use one lexical, POSIX-style repository-relative
representation. Empty paths, the repository-root sentinel `.`, absolute POSIX
and Windows paths, UNC paths, drive-relative paths, and traversal components
are rejected. Backslashes are converted to `/`, dot segments are removed, and
semantic duplicates are deduplicated after canonicalization.

The boundary performs no filesystem resolution, existence check, symlink
resolution, repository search, execution, provider call, or runtime call.

## Scope

This decision changes only the pure localization artifact contract. It does
not define filesystem access or make candidate files authoritative.
