# Arkx

Arkx is an executor-agnostic software-engineering chassis developed through explicit, falsifiable contracts and reproducible evidence.

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
- deterministic architecture, property, metamorphic, mutation-sensitivity, and cross-version verification.

Not implemented:

- concrete executor invocation/orchestration;
- multi-agent runtime;
- product integrations with Codex, Claude Code, Gemini CLI, mini-SWE-agent, SWE-agent, OpenHands, ReX, or other executors;
- end-user Arkx CLI packaging/entrypoint.

Executor-specific mechanisms remain outside the core until an experiment justifies promotion.

## Development posture

Every capability must be introduced through a falsifiable hypothesis, an explicit implementation, an executed experiment, and recorded evidence.

Local success is implementation evidence only:

```text
SCIENTIFIC_SIGNAL != LOCAL_PASS
HYPOTHESIS != IMPLEMENTATION
IMPLEMENTATION != EXECUTED
EXECUTED != ACCEPTED
ACCEPTED != PROMOTED
```

No fallback, executor switch, or scope expansion may be silent.

See [the project contract](docs/project-contract.md), [architecture boundary](docs/architecture.md), and [experimental protocol](docs/experimental-protocol.md).

## Chassis verification

From the repository root:

```text
PYTHONPATH=src python -m arkx.baseline
PYTHONPATH=src python -m unittest discover -s tests -t . -v
python tools/check_foundation.py
python tools/mutation_probe.py
PYTHONPATH=src python tools/chassis_fingerprint.py
```

The CI verifies the suite across Python 3.12, 3.13, and 3.14 and requires the same canonical chassis fingerprint across supported interpreters.

## Product boundary

The current repository exposes Python modules and deterministic contracts. It does not yet contain an installable `arkx` console command or `python -m arkx` entrypoint.

That absence is explicit: the CLI is a future product surface, not an inferred capability of the current chassis.
