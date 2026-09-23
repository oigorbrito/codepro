# P5 patch verification boundary

P5 verifies explicit patch gates and remains separate from final acceptance:

```text
PATCH_VERIFIED != PASS
PATCH_VERIFICATION != SMAG_FINAL_ACCEPTANCE
```

The verifier checks reproduction, patch application, required regression results, post-patch reproduction, expected scope, and evidence references. Missing observations are `UNKNOWN` or `BLOCKED` according to the gate; they are never fabricated as passes.

`VERIFIED`, `REJECTED`, `BLOCKED`, and `UNKNOWN` are P5 statuses. P5 never updates `ExecutionRecord.status` and has no semantic diff analyzer.

The fixture is `PATCH_VERIFICATION_FIXTURE`, not a production acceptance benchmark.

