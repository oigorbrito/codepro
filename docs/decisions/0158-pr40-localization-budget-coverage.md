# Decision 0158: localization budget coverage

## Status

Validated as an isolated follow-up to PR40. Promotion is not authorized.

## Decision

Keep the existing C1 localization contract unchanged and add focused negative
tests for every evidence-budget dimension: files, symbols, and context lines.
The artifact remains a deterministic, non-authoritative record and performs no
repository search or execution.

## Scope boundary

This block does not define path normalization or apply edits. Those require a
separate execution-boundary decision before any consumer treats candidate
paths as actionable.
