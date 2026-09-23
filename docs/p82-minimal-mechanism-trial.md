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

P8.2a records infrastructure qualification, not mechanism evidence. The
baseline runner accepts treatment A only, invokes mini-SWE-agent through its public
Python API in a headless worker, and records execution artifacts. It does not
run verification or decide acceptance. Verification and independent
acceptance are explicit, nullable records; missing provider/model identity is
`BLOCKED`, with no fallback.

The Windows runner-v3 qualification adds an explicit Git Bash environment
(`C:\\Program Files\\Git\\bin\\bash.exe`) without changing the model,
prompt, parser, or treatment. The Arkx OpenRouter adapter recognizes provider
error envelopes before action parsing. A retryable `503`/`provider_overloaded`
response is recorded as `BLOCKED` with
`PROVIDER_AVAILABILITY_FAILURE`; it is not converted into a parser or task
failure. The bounded retry policy is an execution-availability policy only.

Artifacts are append-only under `task_id/attempt-N`. Reusing an existing
attempt is rejected rather than silently overwritten. The prospective Wave 0
sample is frozen in `experiments/p82-wave0-task-sample.json` from the official
`SWE-bench/SWE-bench_Verified` test split; its two strata are explicitly
`UNKNOWN` because no auditable prior Arkx stratification was available.

The official acceptance adapter is in `arkx.swebench_authority`. It creates a
SWE-bench prediction without gold patch or grading labels and invokes the
official harness with a unique `run_id`. The frozen Docker Gold authority
returned `resolved: true` for the two Wave 0 tasks recorded under
`logs/evaluation/`; this qualifies the acceptance path and infrastructure only.
Real A runs still
require one exact provider/model/configuration to be frozen. B/C/D and any
mechanism comparison remain out of scope.
