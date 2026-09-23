# ADR 0047 — Recovery lineage in the replay chain

## Decision

`ReplayChain` accepts an optional `recovery_ref`. When present, replay enforces
the causal order `execution → recovery → verification`; when absent, ordinary
runs remain valid. The field is appended to the public dataclass signature to
preserve positional compatibility for existing consumers.

Recovery remains a recorded plan, not an executed action.

## Acceptance

Recovery references replay in order, out-of-order stages fail, and runs without
recovery remain compatible and do not become incomplete solely because the field
is absent.
