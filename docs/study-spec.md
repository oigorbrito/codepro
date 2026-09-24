# Study Spec v1

Study Spec v1 is the pre-execution design contract for empirical CodePro studies. It exists above P0-P6 and does not execute tasks, select an executor, verify a patch, accept a result, or promote architecture.

The contract is intentionally small:

```text
research question
+ falsifiable hypothesis
+ empirical methodology
+ experimental unit
+ workload reference
+ quality attribute and metrics
+ comparator design
+ repetitions
+ stopping rule
+ analysis-plan reference
+ promotion rule
+ environment-contract reference
+ raw-results policy
= frozen study design
```

## Freeze semantics

A valid Study Spec is serialized canonically and content-addressed with SHA-256 before treatment execution.

The content hash proves integrity only. It does **not** prove that the design existed before the result. Every real run must additionally reference an immutable commit/blob containing the frozen Study Spec, and that reference must precede the run.

Changing a frozen design creates a new design identity/version. A treatment run must never silently mutate its governing Study Spec.

## Fail-closed rules

- missing workload -> invalid study design;
- undeclared primary metric -> invalid;
- control equal to treatment -> invalid;
- one repetition without explicit justification -> invalid;
- no comparator without explicit justification -> invalid;
- raw-run persistence may not be disabled.

A frozen Study Spec contains no outcome and cannot produce `PASS`.

## Methodological scope

The initial enumerated methodologies are `BENCHMARKING` and `ENGINEERING_RESEARCH_BENCHMARKING`. This does not claim that all empirical software engineering uses the same quality criteria. A study must choose the methodology appropriate to its research question.

For benchmark-style studies, the workload and setup must be sufficiently specific for replication, stability must be assessed with sufficient repetitions or a documented justification for fewer runs, and all raw runs must be retained for offline analysis.

## Boundary

```text
STUDY_SPEC_FROZEN != STUDY_EXECUTED
STUDY_EXECUTED != ACCEPTED
ACCEPTED != PROMOTED
CONTENT_HASH != TEMPORAL_PRE_REGISTRATION_PROOF
```
