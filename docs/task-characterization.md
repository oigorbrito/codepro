# P1 deterministic task characterization

P1 transforms explicit `TaskSignals` into a versioned `TaskCharacterization`. It is a structural hypothesis for later experiments, not a router or classifier trained for accuracy.

```text
TaskSignals -> deterministic characterization -> TaskCharacterization
```

P1 does not:

- invoke an executor or a model;
- select or authorize an executor;
- route, escalate, retry, replan, or alter acceptance;
- claim real-world classifier accuracy.

## Fail-closed semantics

Missing required signals, contradictory signals, or ambiguity produce:

```text
scope = UNKNOWN
recommended_path = QUALIFICATION_REQUIRED
confidence = LOW
```

Confidence is ordinal (`HIGH`, `MEDIUM`, `LOW`), not a calibrated probability. P1 uses explicit, centralized thresholds in `CharacterizationConfig`; it does not parse language magically.

## Evidence

The serialized characterization preserves input signals, derived counts, closed-enum classification, confidence, reason codes, recommended path, and telemetry. It stores no chain-of-thought.

```text
CHARACTERIZED != ROUTED != EXECUTED != PASS
```

The manifest at `experiments/characterization-fixture.json` is a `CHARACTERIZATION_FIXTURE`: synthetic stability evidence, not a real-world benchmark.

## Telemetry

P1 exposes `characterization_duration_ms`, `characterization_scope`, `characterization_confidence`, `recommended_path`, and `signal_count`. Duration is measured locally by `characterize_timed`; tokens and cost remain P0-unknown because P1 invokes no model.

## State

```text
P1_TASK_CHARACTERIZATION = IMPLEMENTED / EXECUTED / TESTED_WITH_SYNTHETIC_FIXTURES
ROUTING_PROVEN = NOT_CLAIMED
CLASSIFIER_ACCURATE = NOT_CLAIMED
PRODUCTION_READY = NOT_CLAIMED
```

