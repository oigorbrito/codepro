# Experimental protocol

Arkx develops through small, empirical increments. The protocol below is the minimum record required before a capability can be considered for promotion.

## Required record

Each experiment records:

- `id`: stable identifier;
- `hypothesis`: falsifiable statement;
- `scope`: exact systems, inputs, and exclusions;
- `implementation`: what changed, if anything;
- `executor`: the exact executor and version/configuration;
- `procedure`: reproducible steps;
- `expected_signal`: measurable success and failure criteria;
- `result`: `PASS`, `FAIL`, `BLOCKED`, or `NOT_EXECUTED`;
- `evidence`: links or paths to raw evidence and environment facts;
- `acceptance`: explicit reviewer decision and rationale;
- `promotion`: explicit decision to make the change durable, or `NOT_PROMOTED`.

## State separation

The following are distinct claims and must not be inferred from one another:

```text
HYPOTHESIS -> IMPLEMENTATION -> EXECUTED -> ACCEPTED -> PROMOTED
```

An experiment may stop at any state. `BLOCKED` and `NOT_EXECUTED` are not passes. A mechanism passing in isolation does not mean an executor has been adopted.

## Evidence discipline

- Record local evidence separately from upstream or scientific evidence.
- Preserve failures and blocked runs; do not replace them with a fallback result.
- Name every executor switch and every scope expansion before it happens.
- Keep generated artifacts outside version control unless they are small, intentional fixtures.

## Minimal template

Copy this template into a dated experiment record when the first executable capability is introduced:

```yaml
id: EXP-YYYY-MM-DD-name
hypothesis: "..."
scope: "..."
implementation: "..."
executor: "..."
procedure: "..."
expected_signal: "..."
result: NOT_EXECUTED
evidence:
  local: []
  upstream: []
acceptance: "PENDING"
promotion: NOT_PROMOTED
```

