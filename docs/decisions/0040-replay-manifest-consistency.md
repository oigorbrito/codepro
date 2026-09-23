# ADR 0040 — Replay and manifest consistency validation

## Decision

Arkx adds `validate_replay_against_manifest`. It validates that the replay
belongs to the manifest attempt and, when a terminal status was explicitly
recorded, that it matches the manifest state.

The validator reports divergence; it does not choose a source of truth, repair
state, infer missing events, or execute any component.

## Acceptance

Matching replay and manifest pass. Wrong run identity or conflicting declared
status is rejected. Missing declared status remains indeterminate rather than
being inferred.
