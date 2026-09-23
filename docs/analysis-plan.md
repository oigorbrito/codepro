# Analysis Plan v1

The Analysis Plan freezes how raw runs will be converted into statistical claims before outcomes are inspected.

It is deliberately separate from both the Study Spec and the analysis implementation:

```text
Study Spec -> Analysis Plan -> raw runs -> analysis script -> reported results
```

## Required decisions

The plan declares:

- paired, independent, or descriptive-only design;
- primary and secondary metrics;
- estimand;
- summary statistics;
- inferential mode;
- uncertainty method and confidence level when applicable;
- analysis population;
- missing-data treatment;
- treatment of `BLOCKED` runs;
- treatment of protocol deviations;
- multiplicity policy;
- outlier policy;
- analysis-script reference.

The primary metric must match the frozen Study Spec. Secondary metrics must already be declared by the Study Spec.

## Fail-closed rules

A frequentist plan without a valid confidence level is invalid. A descriptive-only design cannot silently request inferential statistics. Missing-data, blocked-run, deviation, multiplicity, and outlier rules cannot be left blank.

This contract does not prescribe one statistical test for all studies. The method must match the frozen design and the observed data characteristics; any justified deviation from the plan is recorded as a protocol deviation rather than silently substituted.

## Boundary

```text
ANALYSIS_PLAN_FROZEN != RESULTS_ANALYZED
ANALYSIS_SCRIPT != ANALYSIS_PLAN
SECONDARY_EXPLORATION != CONFIRMATORY_PRIMARY_CLAIM
BLOCKED != FAILURE != SUCCESS
```
