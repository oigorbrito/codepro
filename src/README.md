# Product boundary

`src/arkx/` contains the executor-agnostic Arkx chassis.

The current product boundary includes deterministic contracts for execution telemetry, characterization, progress assessment, routing/escalation, repository planning, patch verification, handoff accounting, and empirical-study governance.

Concrete executor invocation and orchestration are intentionally outside this boundary. Adding an executor adapter does not make it part of the core architecture by default.
