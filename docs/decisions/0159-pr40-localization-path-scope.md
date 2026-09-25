# Decision 0159: localization path scope

## Status

Validated as an isolated follow-up to PR40. Promotion is not authorized.

## Decision

Localization candidate files must be repository-relative. Absolute paths and
paths containing traversal components are rejected at the pure artifact
boundary. The contract still does not search, read, write, or apply any file.

Candidate symbols remain opaque identifiers; a future symbol resolver must
define and validate its own scope before execution.
