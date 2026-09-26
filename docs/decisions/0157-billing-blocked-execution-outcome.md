# Decision 0157 — explicit billing-blocked execution outcome

## Contract

An execution that cannot start because the authorized provider or CI service
has no available credit must be recorded as `BILLING_BLOCKED`. It is an
infrastructure/control-plane block, not an executor failure, verifier failure,
task failure, or qualification result.

The outcome is valid only when the execution record preserves the external
billing evidence reference. No billing state may be inferred from a missing
runner, a zero invoice, or an absent log alone.

## Hypothesis

Distinguishing billing blocks from generic infrastructure failures will prevent
the qualification process from attributing an account-control failure to the
executor and will keep promotion closed.

## Acceptance criteria

- `ExecutionOutcome.BILLING_BLOCKED` serializes deterministically.
- `assess_trial` returns `QualificationStatus.BLOCKED` for that outcome.
- The observation cannot infer acceptance or executor failure.
- The record retains an evidence reference supplied by the caller.

## Evidence boundary

This contract does not prove that the current GitHub Actions failure is a
billing block. That classification requires the external billing/runner
message to be captured as an evidence reference.
