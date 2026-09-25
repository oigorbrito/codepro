# Decision 0153 — Historical log retention audit

Date: 2026-09-25

## Evidence

The current `logs/` tree contains 29,101 files and approximately 569 MB. Of
that payload, copied workspaces account for approximately 453 MB and nested
repository `.git` objects account for approximately 80 MB. The largest roots
are the P82 treatment runs and mini runtime replay workspaces.

## Classification

These payloads are `ARCHIVE_ONLY` evidence. They must not be imported as
package data, discovered as tests, or treated as current product behavior.
Their raw contents are preserved for provenance and are not normalized in this
block.

Only 228 log paths are tracked by Git, totaling approximately 639 KB. The
large workspace and nested-cache payload is local-only and is not part of the
remote PR surface. This removes the need for a Git-history cleanup in this
block, but does not authorize deleting local evidence.

## Decision

No deletion, compression, relocation, or rewriting is performed. Any future
retention change must name an exact root, preserve a manifest/hash, and be
reviewed as a separate destructive/archival block. The current safe action is
test-discovery isolation and explicit evidence classification.
