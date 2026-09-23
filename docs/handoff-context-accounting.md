# P6 handoff / context accounting

P6 records explicit handoffs and summarizes observable context cost and loss. Unknown byte counts, duplicate counts, and lost-information declarations remain `null`, not zero.

Executor transitions are derived only when both source and target are known. Duplicate metrics are explicit structural inputs; no semantic similarity model is used. `lost_information=[]` means explicitly declared no loss, while `null` means unknown.

`WITHIN_BUDGET`, `BUDGET_EXCEEDED`, and `UNKNOWN` are observations. P6 does not block execution, invoke a chain, or implement orchestration.

The fixture is `HANDOFF_ACCOUNTING_FIXTURE`, not a performance benchmark.

