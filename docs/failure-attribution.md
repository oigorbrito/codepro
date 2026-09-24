# Failure Attribution v1

Failure Attribution separates evidence about the **system under test** from failures or blockers in the apparatus around it.

A run that does not produce a valid task outcome is not automatically evidence that the treatment failed.

## Dispositions

`SYSTEM_FAILURE` is reserved for evidence attributable to the system under test.

`EXTERNAL_BLOCKER` records inability to obtain the intended observation because of a named external domain such as provider availability, environment, harness, verifier, workload, or configuration.

`INVALID_RUN` records an observation that should not be interpreted as a valid treatment result.

`UNKNOWN` remains unknown until evidence supports a narrower attribution.

## Evidence rule

Every attribution must contain:

```text
observed signature
+ attribution basis
+ raw evidence reference
+ retryability statement
+ primary-analysis impact
```

A provider `503/provider_overloaded` before the system under test can act is therefore an external blocker, not an agent/system failure.

## Boundary

```text
BLOCKED != SYSTEM_FAILURE
UNKNOWN != SYSTEM_FAILURE
HARNESS_FAILURE != TREATMENT_FAILURE
PROVIDER_AVAILABILITY != AGENT_CAPABILITY
INVALID_RUN != NEGATIVE_RESULT
```
