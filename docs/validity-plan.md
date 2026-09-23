# Validity Plan v1

The Validity Plan makes the limits of an empirical claim explicit before those limits are summarized in a final report.

A validity section is not useful when it is a generic checklist. Each threat must identify:

```text
claim at risk -> mechanism -> mitigation -> residual risk -> evidence
```

## Construct validity

Every metric declared in the Study Spec must map to an intended construct with a rationale and an explicit limitation. A metric name alone is not evidence that it measures the intended quality.

## Workload and external validity

The plan repeats the exact frozen workload references, identifies the target population, and states why the workload is relevant to that population. A reproducible workload is not automatically representative.

## Engineering-research context

The artifact must record strengths, weaknesses, and limitations. State-of-art alternatives must be referenced, or the absence/impracticality of alternatives must be justified.

## Required dimensions

For the current benchmark-oriented Arkx methodology, at least one claim-linked threat must address:

- construct validity;
- external validity;
- conclusion validity;
- reliability/reproducibility.

Internal-validity threats are added when the study makes a causal claim or the design introduces a relevant confounding mechanism.

## Boundary

```text
VALIDITY_THREAT_LIST != VALIDITY_ARGUMENT
REPRODUCIBLE_WORKLOAD != REPRESENTATIVE_WORKLOAD
METRIC != CONSTRUCT
MITIGATED != ELIMINATED
```
