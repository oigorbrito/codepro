# Experimental protocol

Arkx develops through small, empirical increments. The protocol below is the minimum record required before a capability can be considered for promotion.

## Pre-execution study design

Before the first treatment run of a comparative or benchmark-style study, create and freeze a valid [Study Spec v1](study-spec.md).

The frozen design and the run record are different artifacts:

```text
STUDY_SPEC_FROZEN -> RUNS_EXECUTED -> ANALYSIS -> ACCEPTANCE -> PROMOTION
```

Every real run must record both:

- `study_spec_hash`: the canonical content hash;
- `study_spec_ref`: an immutable commit/blob/object reference containing that exact spec and existing before the run.

A content hash proves integrity, not temporal precedence. Any post-freeze design change requires a new design version/identity or an explicit protocol-deviation record; it may not silently overwrite the governing design.

All individual raw run records must be retained. Aggregates and summaries are derived artifacts and are not substitutes for raw results.

## Required run record

Each experiment run records:

- `id`: stable identifier;
- `study_spec_hash` and `study_spec_ref`;
- `scope`: exact systems, inputs, and exclusions;
- `implementation`: what changed, if anything;
- `executor`: the exact executor and version/configuration;
- `procedure`: reproducible steps;
- `result`: `PASS`, `FAIL`, `BLOCKED`, or `NOT_EXECUTED`;
- `evidence`: links or paths to raw evidence and environment facts;
- `acceptance`: explicit reviewer decision and rationale;
- `promotion`: explicit decision to make the change durable, or `NOT_PROMOTED`.

The research question, hypothesis, workload, metrics, repetitions, stopping rule, analysis-plan reference, comparator design, and promotion rule belong to the frozen Study Spec rather than being selected after observing run results.

## State separation

The following are distinct claims and must not be inferred from one another:

```text
HYPOTHESIS -> STUDY_SPEC_FROZEN -> IMPLEMENTATION -> EXECUTED -> ACCEPTED -> PROMOTED
```

An experiment may stop at any state. `BLOCKED` and `NOT_EXECUTED` are not passes. A mechanism passing in isolation does not mean an executor has been adopted.

## Evidence discipline

- Record local evidence separately from upstream or scientific evidence.
- Preserve failures and blocked runs; do not replace them with a fallback result.
- Name every executor switch and every scope expansion before it happens.
- Keep generated artifacts outside version control unless they are small, intentional fixtures.
- Preserve every raw run used in analysis; aggregate offline.
- Record deviations from the frozen design explicitly.

## Minimal run template

```yaml
id: RUN-YYYY-MM-DD-name
study_spec_hash: "sha256:..."
study_spec_ref: "git:<immutable-commit-or-blob>"
scope: "..."
implementation: "..."
executor: "..."
procedure: "..."
result: NOT_EXECUTED
evidence:
  local: []
  upstream: []
acceptance: "PENDING"
promotion: NOT_PROMOTED
```
