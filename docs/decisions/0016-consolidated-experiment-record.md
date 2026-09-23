# Decision 0016 — Consolidated experiment record

## Status

Accepted as the first complete harness audit block.

## Decision

Persist one immutable `ExperimentRecord` that links protocol version, frozen
input identity, trials, attempts, verification references, acceptance
references and promotion decision reference. Loading the record must validate
that referenced attempts are present and independently validated.

The record is an index and audit boundary; it does not aggregate metrics,
select executors, infer acceptance or promote a component.

## Falsifiable hypothesis

If experiment records are loaded only after cross-validating their attempts and
evidence references, then an experiment with missing attempts or orphaned
promotion evidence cannot appear complete by metadata alone.

## Acceptance criteria

- record persistence is atomic and immutable;
- all recorded attempts are found and valid;
- verification and acceptance references are preserved;
- promotion references are bound to a recorded attempt;
- malformed or incomplete records are rejected;
- focused contract and promotion tests pass.
