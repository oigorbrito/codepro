# Raw-run provenance v1

Every empirical run must remain attributable to the exact study design, code, task, configuration, executor, environment, repetition, and raw execution record that produced it.

The Run Manifest is a separate artifact from the P0 `ExecutionRecord`. P0 describes what happened during execution; the Run Manifest binds that raw observation to the experimental design and provenance needed for later analysis.

## Required binding

```text
frozen Study Spec
      |
      v
Run Manifest
  - study_spec_hash
  - study_spec_ref
  - arkx_commit
  - task_ref
  - configuration_ref
  - repetition_index
  - executor_id + executor_version
  - environment_ref
  - execution_record_ref + execution_record_hash
  - protocol_deviations
      |
      v
raw ExecutionRecord
```

A summary, table, mean, median, success rate, or chart is never a substitute for the individual raw run records.

## Integrity and chronology

The Run Manifest is deterministically serialized and content-addressed. Its hashes prove integrity, not chronology.

Chronology is established by immutable external references: the frozen Study Spec reference must exist before the governed run, and the raw execution record must be retained after the run. Later analysis must consume the referenced raw records rather than reconstructing them from aggregates.

## Protocol deviations

`protocol_deviations=[]` means no deviation was declared for that run. Any deviation must be explicit; silent executor switches, fallback, scope expansion, task substitution, or configuration mutation remain prohibited.

## Boundary

```text
RAW_RUN != AGGREGATE
RUN_MANIFEST != EXECUTION_RESULT
PROVENANCE_COMPLETE != RESULT_ACCEPTED
HASH_INTEGRITY != TEMPORAL_PRECEDENCE
```
