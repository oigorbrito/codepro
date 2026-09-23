# P6 handoff / context accounting

P6 records explicit handoffs and summarizes observable context cost and loss.

Schema v2 distinguishes event count from unique transition pairs: repeated `a -> b` handoffs count as repeated executor transitions rather than being deduplicated. Duplicate handoff IDs are rejected.

Unknown byte/count measurements remain `null`; explicitly measured zero remains `0`. Negative counts are invalid. `lost_information=[]` means explicitly declared no loss, while `null` means unknown.

`WITHIN_BUDGET`, `BUDGET_EXCEEDED`, and `UNKNOWN` are observations. P6 does not block execution, invoke a chain, or implement orchestration.

```text
UNKNOWN != ZERO
UNIQUE_PAIR_COUNT != TRANSITION_EVENT_COUNT
HANDOFF_ACCOUNTING != HANDOFF_AUTHORIZATION
```

The fixture is `HANDOFF_ACCOUNTING_FIXTURE`, not a performance benchmark.
