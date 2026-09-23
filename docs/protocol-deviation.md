# Protocol Deviation v1

A frozen protocol can encounter reality that was not anticipated. CodePro does not solve that by silently rewriting the study.

Every behavior-affecting departure from the frozen design is recorded as a separate Protocol Deviation.

## Examples

- fallback activation;
- executor switch;
- model or provider switch;
- scope expansion;
- task substitution;
- configuration change;
- retry-policy change;
- workload exclusion;
- analysis deviation.

Each record preserves frozen value, observed value, reason, evidence, phase, whether the change was preauthorized, and its declared impact on analysis.

## Fail-closed impact

An unplanned behavior-affecting change cannot simply be labeled `NO_PRIMARY_EFFECT`. If treatment identity changes materially, the defensible default is a new frozen study or an explicitly separated sensitivity analysis.

## Boundary

```text
DEVIATION_RECORDED != DEVIATION_ACCEPTABLE
SILENT_SWITCH != SAME_TREATMENT
TASK_SUBSTITUTION != SAME_WORKLOAD
POST_HOC_ANALYSIS_CHANGE != PREDECLARED_ANALYSIS
REQUIRES_NEW_STUDY != RETRY_SAME_RUN
```
