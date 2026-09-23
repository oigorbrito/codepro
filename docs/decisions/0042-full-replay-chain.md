# ADR 0042 — Full explicit replay chain

## Decision

Arkx adds `ReplayChain` and `replay_chain` for explicit references across
request, plan, execution, verification, acceptance, and promotion. The reducer
validates run identity and causal stage order, but leaves absent stages as
`None`.

Replay is an audit operation. It does not execute, verify, accept, promote, or
invent references for missing artifacts.

## Acceptance

An ordered explicit chain round-trips into the corresponding references; an
out-of-order stage is rejected; and incomplete chains remain incomplete.
