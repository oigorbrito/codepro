# P0 baseline metrics

P0 establishes measurement semantics; it does not establish a performance baseline.

| Metric | Meaning | Unknown representation |
| --- | --- | --- |
| `acceptance_status` | Explicit final execution status, including `UNVERIFIED` when evidence is insufficient | `NOT_EXECUTED` before a task finish event |
| `tokens` | Observed input, output, and total token usage from events | JSON `null` when not observed |
| `cost` | Observed monetary cost from events or executor metadata | JSON `null` when not observed |
| `wall_time` | Elapsed time between first `TASK_STARTED` and last `TASK_FINISHED` | JSON `null` when either boundary is absent |
| `retries` | Count of explicit `RETRY` events | `0` means no such events were recorded |
| `replans` | Count of explicit `REPLAN` events | `0` means no such events were recorded |
| `executor_invocations` | Count of `EXECUTOR_STARTED` events | `0` means no such events were recorded |
| `handoffs` | Count of explicit `HANDOFF` events | `0` means no such events were recorded |
| `human_interventions` | Count of explicit `HUMAN_INTERVENTION` events | `0` means no such events were recorded |

Counts are event-derived. Resource measurements are nullable: unknown tokens are not zero tokens, and unknown cost is not zero cost.

## Boundary

`TASK_FINISHED` with a requested `PASS` but no `EVIDENCE_ADDED` reference resolves to `UNVERIFIED`. P0 does not verify evidence quality and does not turn an executor claim into acceptance.

```text
P0 DOES NOT CLAIM PERFORMANCE
P0 ONLY MAKES PERFORMANCE MEASURABLE
```

The deterministic fixture can be run with:

```text
PYTHONPATH=src python -m arkx.baseline
```

No real run artifacts are committed by the test suite.

