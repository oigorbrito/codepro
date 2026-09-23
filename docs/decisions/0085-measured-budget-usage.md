# ADR 0085: Budget usage must be measured at the execution boundary

## Status

Accepted for local architectural evidence; external qualification unchanged.

## Decision

`BudgetLedger.record_usage()` records measured token, wall-time and cost usage
for an attempt already admitted by the ledger. Orchestration requires the
measurements corresponding to declared finite limits. If a runner does not
provide a required measurement, the result is explicitly blocked with
`BUDGET_USAGE_UNAVAILABLE`; usage is never inferred as zero. If measured usage
exceeds a limit, the result is explicitly blocked with
`EXECUTION_BUDGET_EXHAUSTED` after retaining the execution evidence.

## Falsifiable hypothesis and acceptance criteria

H1: a runner cannot appear budget-compliant merely because it returned an
execution result. Tests must accept recorded measured usage, reject usage for
an unconsumed attempt, and block orchestration when required measurement is
missing.

## Consequences

Concrete adapters must expose canonical `total_tokens`, `wall_time_ms`, and
`cost` fields when the plan declares those limits. Zero is a valid measured
value; missing is not equivalent to zero. Adapter-specific raw usage may still
be retained alongside the canonical fields.
