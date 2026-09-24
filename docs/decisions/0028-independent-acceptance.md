# ADR 0028: Independent acceptance decision

## Status

Accepted for implementation in issue #7.

## Hypothesis

If acceptance is a separate, identity-bound decision after governed execution
and verification, promotion cannot be inferred from local test success or from
the executor's own report.

## Contract

`decide_acceptance` consumes a governed execution record, an explicitly
identified authority, a stable run identifier, and evidence references. It
returns exactly one auditable status: `ACCEPTED`, `REJECTED`, `INDETERMINATE`,
`BLOCKED`, or `NOT_EXECUTED`. Acceptance requires a verified record, an
independent authority, matching authority binding, execution and verification
artifacts, and non-empty evidence. The function does not promote artifacts.

## Falsifiable acceptance criteria

1. A verified record with matching independent authority and complete evidence
   returns `ACCEPTED` and preserves the run/evidence references.
2. Missing or mismatched authority, missing evidence, and non-independent
   authority remain `BLOCKED`.
3. A rejected verification returns `REJECTED`; governance-blocked execution
   remains `BLOCKED`; no execution cannot become acceptance.
4. Focused tests cover all boundaries and the complete local suite is recorded
   separately from upstream CI evidence.

## Evidence

The implementation and executable tests are the evidence for this contract.
The GitHub check run for the pull request is the independent CI evidence; local
test results are environment-scoped and do not qualify a provider or benchmark.
