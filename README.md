# Arkx

Arkx is a greenfield project for empirical, incremental development of reliable capability.

> **MINIMUM SUFFICIENT ARCHITECTURE**  
> **FOR MAXIMUM RELIABLE CAPABILITY**

This repository is the canonical root for the project. It intentionally contains only the foundation in this bootstrap: the project contract, experimental protocol, structural placeholders, and a minimal CI check.

## Scope of this bootstrap

Included:

- explicit project invariants;
- a small, evidence-oriented experimental protocol;
- stable top-level boundaries for future work;
- a deterministic structural check and minimal CI.

Deferred:

- routing and planning;
- multi-agent orchestration;
- OpenHands, ReX, mini-SWE-agent, and SWE-agent integrations;
- product dependencies or automatic migration from `smag-rex`.

## Development posture

Every capability must be introduced through a falsifiable hypothesis, an explicit implementation, an executed experiment, and recorded evidence. Local success is not scientific or upstream evidence. No fallback, executor switch, or scope expansion may be silent.

See [the project contract](docs/project-contract.md) and [the experimental protocol](docs/experimental-protocol.md).

## P0 baseline and telemetry

P0 provides executor-agnostic execution records, explicit event metrics, nullable resource measurements, and fail-closed status resolution. It does not implement performance optimization, routing, planning, or any executor. See [the P0 metrics contract](docs/baseline-metrics.md).

Run the deterministic fixture and tests locally from the repository root:

```text
PYTHONPATH=src python -m arkx.baseline
PYTHONPATH=src python -m unittest discover -s tests -t . -v
```

P1 adds deterministic task characterization from explicit signals only. See [the P1 contract](docs/task-characterization.md). It does not select executors or route work.

## Checks

The bootstrap check is dependency-free:

```text
python tools/check_foundation.py
```
