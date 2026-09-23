# ADR 0032 — Attempt-store lineage validation and replay visibility

## Decision

`AttemptSnapshot` exposes optional `RetryLineage` when
`retry-lineage.json` is present. `load_attempt` validates the lineage against
the manifest, trial, attempt number, and configuration digest.

Historical attempts without the new artifact remain loadable with
`retry_lineage=None`. This preserves compatibility while making missing lineage
explicit; the reader never infers a retry chain from the attempt number alone.

## Acceptance

Valid lineage round-trips and is returned by the reader. Drift is rejected.
Legacy attempts remain readable but expose missing lineage explicitly.
