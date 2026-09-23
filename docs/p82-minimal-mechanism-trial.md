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
