# Decision 0018 — Contract execution lifecycle

## Status

Accepted as the third architecture strengthening block.

## Decision

Represent one contract execution as a `ContractRun` containing the request,
execution result, lifecycle history and optional verification/acceptance
evidence. The executor cannot create verification or acceptance implicitly.

## Falsifiable hypothesis

If a fake executor can traverse completed and blocked flows while verification
and acceptance remain optional independent attachments, then orchestration can
be tested without a concrete model or provider.

## Acceptance criteria

- completed fake execution preserves lifecycle history;
- completed execution alone is not accepted;
- independent verification plus acceptance can be attached explicitly;
- blocked execution requires structured error and is not accepted;
- no real executor/provider is invoked or promoted.
