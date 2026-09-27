# Reconciliation R3 — telemetry / evidence boundary

**Status:** DONE

## Decision

CodePro has one canonical generic execution telemetry boundary:

    arkx.contracts.ExecutionRecord

The restored Python contract retains:

- task/run/executor identity;
- start/finish timestamps;
- explicit execution status and decision reason;
- input/output/total tokens;
- nullable monetary cost;
- wall time;
- retry/replan/executor/handoff/human-intervention counts;
- evidence references;
- errors;
- metadata;
- versioned deterministic serialization and persistence.

The TypeScript runtime record is preserved as a specialized measurement
boundary:

    LocalInferenceMeasurementRecordV1

It retains the complete post-deviation local-inference measurement work,
including model/artifact/quantization/runtime/platform configuration,
CPU/CUDA configuration, memory measurements, throughput, termination/cost
semantics and raw evidence references.

The two records correlate through `run_id`.

    GENERIC EXECUTION RECORD
        !=
    LOCAL INFERENCE MEASUREMENT RECORD

## Compatibility

Previous TypeScript names remain exported as compatibility aliases:

    ExecutionRecordV1
    validateExecutionRecord
    serializeExecutionRecord
    persistExecutionRecord

They do not establish a second canonical generic telemetry boundary.

## Existing evidence contracts

The following restored contracts remain authoritative in their respective
roles:

    MeasurementContract
        -> metric operational semantics

    RunManifest
        -> provenance and content binding

    EventLog
        -> event integrity / sequence / decision history

No local-inference measurement value was copied into generic execution fields
when the semantic meaning was not equivalent.

    UNKNOWN != ZERO

The existing Phase-2 runtime telemetry fixture was preserved rather than
rewritten.

## Verification

Before reconciliation:

    PythonTelemetryContracts      = PASS
    TypeScriptInferenceTelemetry = PASS

After semantic reconciliation:

    PythonCanonicalTelemetry     = PASS
    LocalInferenceMeasurement    = PASS
    TypeScriptTypecheck          = PASS
    FrontendBuild                = PASS

## Gate

    ONE_CANONICAL_GENERIC_EXECUTION_RECORD = PASS
    LOCAL_INFERENCE_FIELDS_PRESERVED       = PASS
    RAW_EVIDENCE_REFERENCES_PRESERVED      = PASS
    UNKNOWN_SEMANTICS_PRESERVED            = PASS
    PROVENANCE_BOUNDARY_PRESERVED          = PASS
    EVENT_LOG_BOUNDARY_PRESERVED           = PASS
    NO_FABRICATED_PHASE2_VALUES            = PASS

    R3 = DONE
