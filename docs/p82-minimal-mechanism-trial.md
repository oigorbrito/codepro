# P8.2 — Minimal mechanism trial

P8.2 defines a controlled A/B/C/D design with a fixed executor. The harness
creates deterministic trial plans; it does not invoke an LLM or executor,
apply a mechanism, verify a patch, accept a result, or select a winner.

| Arm | Treatment |
| --- | --- |
| A | mini baseline |
| B | A + safe editor |
| C | A + enhanced repository context |
| D | A + safe editor + enhanced repository context |

All tasks, replicates, executor identity, exact model, environment, budget,
verification contract, and acceptance authority are frozen in
`P82ExperimentConfig`. Missing control evidence remains `UNKNOWN`; it is never
converted to a default or zero. A result must later be recorded through the
P8.1 `ExecutorTrial` contract with `Treatment` set to the corresponding arm.

The primary outcomes are independently verified acceptance and cost to
acceptance. False-pass rate is a guardrail. P8.2 produces no promotion or
executor-adoption decision.

The run manifest also records protocol version, model/temperature/reasoning
configuration, task sample and stratum, attempts, token/cost/wall-time limits,
verification identity, and independent acceptance identity. Task provenance is
evidence metadata only; it grants no authority to a task or treatment.

Run comparison is tri-state: `COMPARABLE` means controls are known and equal,
`NOT_COMPARABLE` means a confounder differs, and `INDETERMINATE` means a
required control is unknown. Summaries retain `NOT_EXECUTED` and `BLOCKED`
counts, aggregate only observed metrics, and never produce a winner or a
promotion decision.

## P8.2a baseline execution path

P8.2a is infrastructure qualification, not mechanism evidence. The baseline
runner accepts treatment A only, invokes mini-SWE-agent through its public
Python API in a headless worker, and records execution artifacts. It does not
run verification or decide acceptance. Verification and independent
acceptance are explicit, nullable records; missing provider/model identity is
`BLOCKED`, with no fallback.

Artifacts are append-only under `task_id/attempt-N`. Reusing an existing
attempt is rejected rather than silently overwritten. No prospective task
sample is committed until public task artifacts, selection rationale, and an
independent acceptance authority are available.
