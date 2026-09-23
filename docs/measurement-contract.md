# Measurement Contract v1

A metric name is not a measurement definition. The Measurement Contract freezes the operational semantics used to turn run evidence into values.

For every metric it records:

- data type;
- unit;
- direction of preference, when meaningful;
- source of the observation;
- measurement rule;
- missing/unknown semantics;
- invalid-run semantics;
- precision rule.

Every metric named by the frozen Study Spec must have an operational definition before confirmatory analysis.

## Missingness

Unknown, unavailable, blocked, and not-observed values are never silently converted to zero. A measured zero is an observation; missingness is absence of that observation and is handled by the frozen Analysis Plan.

## Separation from construct validity

The Measurement Contract states **how a value is obtained**. The Validity Plan states **why that value is relevant to the intended construct and where that interpretation is limited**.

## Boundary

```text
METRIC_NAME != OPERATIONAL_DEFINITION
UNKNOWN != ZERO
INVALID_RUN != MEASURED_FAILURE
MEASUREMENT_RULE != CONSTRUCT_VALIDITY_ARGUMENT
DISPLAY_ROUNDING != RAW_MEASUREMENT
```
