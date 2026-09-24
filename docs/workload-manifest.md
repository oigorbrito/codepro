# Workload Manifest v1

The Workload Manifest freezes the task population used by an empirical study so that task substitution, treatment-specific filtering, and order changes cannot occur silently after outcomes are visible.

## Required description

A workload declares:

- source and source version;
- target population the workload is intended to represent;
- sampling strategy;
- deterministic selection rule and its justification;
- inclusion and exclusion criteria;
- the exact ordered task references;
- holdout policy;
- task-order policy;
- random seed whenever sampling or ordering is randomized.

The manifest is canonicalized and content-addressed before treatment execution.

## Interpretation

A valid manifest proves that the selected workload is explicit and reproducible. It does **not** prove that the workload is representative of every real software-engineering task. Representativeness and construct validity require a separate validity argument.

## Boundary

```text
FROZEN_WORKLOAD != REPRESENTATIVE_POPULATION_PROVEN
TASK_SUBSTITUTION != SAME_EXPERIMENT
RANDOMIZED_WITHOUT_SEED != REPRODUCIBLE
QUALIFICATION_RULE != TREATMENT_OUTCOME
```

Task exclusions discovered after freeze are protocol deviations; they must not be silently removed from one treatment arm.
