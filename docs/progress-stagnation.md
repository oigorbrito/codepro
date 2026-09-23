# P2 progress / stagnation detection

P2 compares explicit `ProgressSnapshot` values and emits evidence-only assessments:

```text
PROGRESS_PROVEN
PROGRESS_NOT_PROVEN
NO_PROGRESS
UNKNOWN
```

P2 observes progress. P2 does not control execution, authorize retries, authorize replans, select or switch executors, route work, escalate automatically, produce `PASS`, or change acceptance.

## Semantics

- New relevant files, new passing tests, newly explained failures, reduced acceptance distance, or reduced diff distance are observable progress evidence.
- The same failure signature with no new evidence can establish `NO_PROGRESS`.
- Repeated actions with unchanged acceptance distance can establish `NO_PROGRESS`.
- A new failure with new useful evidence is not treated as stagnation.
- Missing required measurements and contradictory distance values are `UNKNOWN`.
- `confidence` is ordinal (`HIGH`, `MEDIUM`, `LOW`), not a calibrated probability.

The required measurement fields are centralized in `ProgressConfig`. Defaults require all snapshot fields, so missing telemetry fails closed.

## Policy boundary

P2 exposes no retry or replan policy. Future policy may consume `ProgressAssessment` and independently derive a justification; this module performs no action.

```text
PROGRESS_PROVEN != PASS
NO_PROGRESS != FAILED
UNKNOWN != PASS
```

The manifest at `experiments/progress-detection-fixture.json` is a `PROGRESS_DETECTION_FIXTURE`, not a real benchmark.

## Telemetry

Assessments expose `progress_status`, `progress_confidence`, `progress_signal_count`, `repeated_action_count`, `failure_signature_count`, and `assessment_duration_ms`. No tokens or cost are fabricated.

## State

```text
P2_PROGRESS_DETECTION = IMPLEMENTED / EXECUTED / TESTED_WITH_SYNTHETIC_FIXTURES
STAGNATION_POLICY_PROMOTED = NOT_CLAIMED
RETRY_POLICY_PROVEN = NOT_CLAIMED
PRODUCTION_READY = NOT_CLAIMED
```

