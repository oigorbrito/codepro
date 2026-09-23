# ADR 0100: Recovery lineage is part of audited attempt loading

## Status

Accepted for local architectural evidence.

## Decision

`load_attempt()` reads and validates `recovery-lineage.json` when present.
Recovery lineage must match the manifest's trial, attempt, attempt number and
configuration digest. An attempt cannot contain both retry and recovery
lineage, because that would make the causal origin ambiguous.

## Falsifiable hypothesis and acceptance criteria

H1: recovery lineage written by the artifact store cannot be silently ignored
or drift from the loaded manifest. Tests must round-trip valid lineage and
reject an invalid source identity.

## Consequences

Audit and comparison consumers can distinguish ordinary retry from recovery.
The manifest still needs explicit policy fields if future workflows permit
multiple recovery types.
