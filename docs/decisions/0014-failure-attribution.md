# ADR 0014 — Separate treatment failure from experimental blockers

## Status

Accepted for the Arkx empirical chassis.

## Observed need

Real qualification runs can be prevented by provider overload, harness failure, verifier defects, environment problems, invalid workload instances, or configuration errors. Treating every unsuccessful run as a treatment failure biases comparisons and conflates measurement-apparatus reliability with system capability.

## Decision

Add Failure Attribution v1 with explicit dispositions and domains.

A `SYSTEM_FAILURE` can only be assigned to the system-under-test domain. External blockers must name an external domain. Unknown causes remain `UNKNOWN` until evidence supports a narrower attribution. Every attribution requires raw evidence.

## Alternatives considered

- Count every non-pass as failure: rejected because it mixes treatment effects with experimental infrastructure failures.
- Drop blocked runs silently: rejected because missingness can be informative and must follow the frozen Analysis Plan.
- Retry until a usable result appears: rejected unless retries are bounded and frozen in protocol because outcome-dependent retrying can bias the sample.

## Limitation

This contract prevents category collapse but does not make root-cause analysis infallible. Attribution quality still depends on evidence, and ambiguous cases must remain unknown.

## Rollback/removal condition

Replace this contract if the experiment harness acquires an equivalent or stronger evidence-bound failure taxonomy without collapsing blocked, invalid, unknown, and treatment-failure states.
