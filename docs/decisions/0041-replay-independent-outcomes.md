# ADR 0041 — Independent verification and acceptance in replay

## Decision

`ReplayState` records `verification_state` and `acceptance_decision` only when
explicitly present in event data. `validate_replay_outcomes` compares those
values with independent evidence when supplied.

Execution completion does not imply verification, and verification does not
imply acceptance. Missing outcome events remain missing.

## Acceptance

Matching independent evidence passes; conflicting verification or acceptance is
rejected; absent outcome data is not inferred from execution state.
