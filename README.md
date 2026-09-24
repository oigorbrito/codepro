# CodePro

CodePro is an executor-agnostic software-engineering chassis developed through explicit, falsifiable contracts and reproducible evidence.

> **MINIMUM SUFFICIENT ARCHITECTURE**  
> **FOR MAXIMUM RELIABLE CAPABILITY**

This repository is the canonical root for the project.

## Current scope

Implemented:

- P0 executor-agnostic execution contracts and telemetry;
- P1 deterministic task characterization;
- P2 deterministic progress/stagnation assessment;
- P3 bounded rule-based routing and escalation;
- P4 repository planning/state artifacts;
- P5 patch verification;
- P6 handoff/context accounting;
- frozen Study Spec, Workload, Treatment, Measurement, Analysis, Validity, Promotion, Environment, Deviation, Failure Attribution, and Run Provenance contracts;
- fail-closed deserialization and evidence semantics;
- deterministic architecture, property, metamorphic, mutation-sensitivity, and cross-version verification;
- a minimal installable CLI boundary with no runtime dependencies;
- a low-level command observation boundary with no task-status inference;
- capability qualification and executor binding contracts that distinguish availability from qualification and refuse hidden ranking;
- request/governance authority contracts for explicit scope, permissions, execution budgets, environment, and independent acceptance authority;
- version-freshness governance that separates historical controls from current candidates and requires requalification for materially stale external components.

Not implemented:

- concrete Codex/Claude/Gemini executor adapters or orchestration;
- multi-agent runtime;
- product integrations with Codex, Claude Code, Gemini CLI, mini-SWE-agent, SWE-agent, OpenHands, ReX, or other executors;
- interactive TUI;
- CLI task execution.

Executor-specific mechanisms remain outside the core until an experiment justifies promotion.

## CLI

Install the current checkout:

```text
python -m pip install --no-deps -e .
```

Then:

```text
codepro --help
codepro --version
codepro doctor
codepro inspect
codepro inspect --json
```

The equivalent module entrypoint is:

```text
python -m arkx --help
```

The public product command is `codepro`. The Python implementation namespace remains `arkx` for now so the CLI introduction does not also become a package-rename migration.

Running `codepro` with no arguments prints help and performs no task execution.

`codepro inspect` is observational only. It may invoke read-only Git queries and inspect filesystem markers/PATH, but it does not modify the repository, select an executor, or execute a task.

The internal command primitive is also observational: a process exit code, timeout, or environment error is recorded as raw execution evidence. It does not infer task success/failure, verification, acceptance, or promotion.

## Development posture

Every capability must be introduced through a falsifiable hypothesis, an explicit implementation, an executed experiment, and recorded evidence.

Local success is implementation evidence only:

```text
SCIENTIFIC_SIGNAL != LOCAL_PASS
HYPOTHESIS != IMPLEMENTATION
IMPLEMENTATION != EXECUTED
EXECUTED != ACCEPTED
ACCEPTED != PROMOTED
LATEST != BEST
HISTORICAL_CONTROL != CURRENT_CANDIDATE
```

No fallback, executor switch, scope expansion, or external-component version substitution may be silent.

See [the project contract](docs/project-contract.md), [version freshness policy](docs/version-freshness-policy.md), [architecture boundary](docs/architecture.md), and [experimental protocol](docs/experimental-protocol.md).

## Chassis verification

From the repository root:

```text
PYTHONPATH=src python -m arkx.baseline
PYTHONPATH=src python -m unittest discover -s tests -t . -v
python tools/check_foundation.py
PYTHONPATH=src python tools/mutation_probe.py
PYTHONPATH=src python tools/chassis_fingerprint.py
```

The CI installs the CLI and verifies the suite across Python 3.12, 3.13, and 3.14 while requiring the same canonical chassis fingerprint across supported interpreters.
