# P5 patch verification boundary

P5 verifies explicit patch gates and remains separate from final acceptance:

```text
PATCH_VERIFIED != PASS
PATCH_VERIFICATION != SMAG_FINAL_ACCEPTANCE
```

The verifier records `reproduces_issue_before_patch` and `reproduces_issue_after_patch`; `True` means the issue reproduces and `False` means it does not. A reparative reproduction gate therefore requires `before=True` and `after=False`. Missing observations are `UNKNOWN` or `BLOCKED` according to the gate; they are never fabricated as passes.

`VERIFIED`, `REJECTED`, `BLOCKED`, and `UNKNOWN` are P5 statuses. P5 never updates `ExecutionRecord.status` and has no semantic diff analyzer.

The fixture is `PATCH_VERIFICATION_FIXTURE`, not a production acceptance benchmark.
