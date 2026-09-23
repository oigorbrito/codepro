# P3 rule-based routing and evidence-based escalation

P3 is the first bounded policy layer. It consumes P1 characterization, P2 progress assessment, external evidence sufficiency, and an explicit budget. It produces serializable decisions only.

```text
characterization -> select initial path -> bounded outcome -> evidence/progress -> continue | stop | escalate
```

## Routing

P1 scope maps directly to a path:

```text
SIMPLE          -> SIMPLE_PATH
LOCALIZED       -> LOCALIZED_PATH
REPOSITORY_WIDE -> REPOSITORY_WIDE_PATH
UNKNOWN         -> QUALIFICATION_REQUIRED
```

P3 validates that P1's `recommended_path` agrees with the scope. It does not infer a better path or choose a concrete executor.

## Escalation

The path ladder is monotonic:

```text
SIMPLE_PATH -> LOCALIZED_PATH -> REPOSITORY_WIDE_PATH
```

`NO_PROGRESS` plus an available higher path and escalation budget produces `ESCALATE`. At the top of the ladder it produces `BLOCK`. A failed attempt alone is not an escalation reason.

`PROGRESS_PROVEN` plus `SUFFICIENT` evidence produces `STOP_SUFFICIENT_EVIDENCE`, never `PASS`. `UNKNOWN` progress or evidence requires qualification. Insufficient evidence may continue while attempt budget remains.

## Budget

Defaults are conservative and explicit:

```text
max_path_escalations = 2
max_attempts = 3
```

The policy returns a derived budget snapshot. It does not execute an attempt, increment retry policy, or mutate P0 telemetry.

## Boundaries

```text
ROUTE BEFORE CASCADING
ESCALATE ON EVIDENCE
NO_SILENT_EXECUTOR_SWITCH
NO_UNBOUNDED_CHAIN
NO_PROGRESS != AUTOMATIC_FAILURE
CHARACTERIZATION != ACCEPTANCE
ROUTING != ACCEPTANCE
ESCALATE != invoke another executor
```

P3 is rule-based, does not learn, does not invoke executors, does not own acceptance, and does not implement retry, replan, planner, multi-agent, or executor selection behavior. The fixture at `experiments/routing-escalation-fixture.json` is synthetic policy evidence, not an accuracy benchmark.

## State

```text
P3_ROUTING_ESCALATION = IMPLEMENTED / EXECUTED / TESTED_WITH_SYNTHETIC_FIXTURES
EXECUTOR_SELECTION = NOT_IMPLEMENTED
LEARNED_ROUTING = NOT_IMPLEMENTED
ROUTING_PROMOTED = NOT_CLAIMED
PRODUCTION_READY = NOT_CLAIMED
```

