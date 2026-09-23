# ADR 0063 — Audited loading is an explicit artifact-store boundary

## Decision

`AttemptStore.load_audited()` loads the validated attempt snapshot and invokes
the read-only restored-chain audit before returning an audit result. The
existing `load_attempt()` and `list_attempts()` paths remain available for
compatibility, but consumers that require comparison, acceptance, or
promotion integrity can opt into audited loading explicitly.

The store does not select a winner, rerun execution, or infer missing event
stages. Audit results remain `INCOMPLETE` when the persisted chain is partial.

## Falsifiable hypothesis

Audited loading always passes the restored snapshot through chain validation,
while legacy loading behavior remains unchanged. Tests falsify this if the
audited path bypasses validation or if loading causes external execution.

## Acceptance evidence

The complete local suite ran 311 tests successfully on Python 3.11.9 with
`PYTHONPATH=src`. Tests verify that `AttemptStore.load_audited()` delegates to
the restored-chain audit and preserves the loaded snapshot boundary.

## Status

Accepted for integrity-sensitive artifact consumers. No external execution or
promotion is performed during loading.
