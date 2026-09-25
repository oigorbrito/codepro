# Decision 0151 — PR30 non-code disposition

Date: 2026-09-25

## Inventory

The PR30 delta contains 127 documentation files, 228 log files, and 12
experiment fixtures relative to `origin/main`. The logs include raw runs,
workspaces, and at least one nested repository cache with its own `.git`
objects. These are not interchangeable with product source files.

## Classification

- Decision records, protocol pages, and release/qualification plans:
  `HISTORICAL_NORMATIVE_CANDIDATE`. Preserve until each is mapped to the
  current authority; duplicate or superseded records must not silently become
  current policy.
- JSON experiment fixtures:
  `EXPERIMENT_INPUT_CANDIDATE`. Keep only when a current test or protocol
  references them; otherwise classify as historical.
- Raw JSON/log/trajectory/report artifacts:
  `HISTORICAL_EVIDENCE`. Preserve provenance and keep them outside test
  discovery.
- Nested workspaces, repository caches, and copied source trees under `logs/`:
  `ARCHIVE_ONLY`. They are evidence payloads, not runtime inputs or package
  data; their size and nested repositories require an explicit archival/removal
  decision before any deletion.

## Decision

No non-code artifact is deleted in this block. The only safe immediate action
is classification and discovery isolation. The previous deletion of the
explicitly identified mini-adaptation helper files remains separate and is not
expanded to historical evidence.

## Next gate

The fixture/reference audit is complete. Historical logs remain unchanged;
their retention or archival requires an exact path set and owner.

## Fixture audit result

All 12 added JSON fixtures parsed successfully. Nine are referenced directly
by tests or by another current protocol artifact. Three have no active
reference detected outside themselves: `cost-tier-comparison-protocol.json`,
`p82-block3-t1-functional-v2.json`, and `p82-wave0-comparison-protocol.json`.
They are classified `HISTORICAL_UNREFERENCED_CANDIDATE`, not deleted.

## Decision-record audit

All decision Markdown files have no broken local references under the checked
`docs/decisions/` and `logs/architecture/` paths. The six duplicate IDs were
normalized in an isolated worktree and then applied here:

- 0031 package boundary → 0112
- 0032 minimal CLI → 0113
- 0033 MVP vertical contract → 0114
- 0034 neutral verifier boundary → 0115
- 0035 executor qualification protocol → 0116
- 0037 second-executor enablement → 0152

The earlier lineage/persistence records retain their IDs. After the change,
duplicate numeric IDs are zero and old filename references are zero. No
document content was deleted.
