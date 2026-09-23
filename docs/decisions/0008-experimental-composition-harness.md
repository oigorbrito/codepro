# 0008 — Experimental composition harness

- Status: experimental contract
- Date: 2026-09-22

P7 introduces only declarative treatment and observation contracts. The harness keeps the five controlled dimensions explicit, canonicalizes mechanism order, rejects duplicate treatment names and semantic compositions, and distinguishes `COMPARABLE`, `INCOMPARABLE`, and `UNKNOWN`.

P7 does not invoke P1–P6 or any executor. A treatment can record that a mechanism is enabled without granting that mechanism execution authority. The initial treatment matrix is A–F; adaptive composition G is deferred until an adaptive mechanism is qualified.
