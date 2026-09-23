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

P7 composition trials use their own comparability namespace: `COMPARABLE`, `INCOMPARABLE`, and `UNKNOWN`. P7 records externally supplied measurements and does not convert them into acceptance results.

P8.1 adds executor qualification records with explicit `EXECUTOR` and `TREATMENT` comparison axes. P8.1 records externally supplied execution outcomes and acceptance observations; it does not execute an executor, infer acceptance, rank executors, or promote components.

P8.2 defines the minimal mechanism trial as a declarative A/B/C/D plan over a
fixed executor: baseline, safe editor, enhanced repository context, and their
combination. Its harness freezes task, replicate, executor, model,
environment, budget, verification, and independent acceptance authority. It
does not invoke an executor or mechanism and does not manufacture acceptance;
results remain P8.1 observations. Missing controls and measurements remain
`UNKNOWN`, and the only intended treatment difference is the declared arm.
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
