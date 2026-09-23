# P5 patch verification boundary

P5 verifies explicit patch gates and remains separate from final acceptance:

```text
PATCH_VERIFIED != PASS
PATCH_VERIFICATION != FINAL_ACCEPTANCE
```

Schema v2 uses directionally explicit reproduction fields:

- `issue_reproduced_before_patch=True` means the defect was observed before treatment;
- `issue_reproduces_after_patch=False` means the defect no longer reproduces after treatment.

The old ambiguous `reproduction_passed_after_patch` representation is not retained as an alias.

When issue reproduction is required, both pre-patch and post-patch observations are required. When reproduction is explicitly not applicable, those fields may remain unknown without fabricating a gate.

The verifier also checks patch application, required regression results, expected scope, and evidence references. Missing observations are `UNKNOWN` or `BLOCKED` according to the gate; they are never fabricated as passes.

`VERIFIED`, `REJECTED`, `BLOCKED`, and `UNKNOWN` are P5 statuses. P5 never updates `ExecutionRecord.status`.

The fixture is `PATCH_VERIFICATION_FIXTURE`, not a production acceptance benchmark.
