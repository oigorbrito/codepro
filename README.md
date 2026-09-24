# Codepro

Codepro is a repository for incremental implementation and empirical
evaluation of software capability.

The current Python import namespace is `arkx` for compatibility; the product,
distribution, CLI, and release identity are `codepro`.

> **MINIMUM SUFFICIENT ARCHITECTURE**  
> **FOR MAXIMUM RELIABLE CAPABILITY**

This repository is the canonical root for the project. It contains runtime
contracts, an execution harness, the project contract, the experimental
protocol, and structural checks.

## Current scope

Included:

- explicit project invariants;
- an evidence-oriented experimental protocol;
- stable top-level boundaries;
- a deterministic structural check, executable contracts, and a Treatment A
  baseline harness.

Still deferred or unqualified:

- multi-agent orchestration;
- OpenHands, ReX, and SWE-agent integrations;
- real provider/model adoption and the A/B/C/D mechanism trial;
- product dependencies or automatic migration from `smag-rex`.

## Development posture

Every capability must be introduced through a falsifiable hypothesis, an explicit implementation, an executed experiment, and recorded evidence. Local success is not scientific or upstream evidence. No fallback, executor switch, or scope expansion may be silent.

See [the project contract](docs/project-contract.md) and [the experimental protocol](docs/experimental-protocol.md).

## P0 baseline and telemetry

P0 provides executor-agnostic execution records, explicit event metrics, nullable resource measurements, and fail-closed status resolution. It does not implement performance optimization, routing, planning, or any executor. See [the P0 metrics contract](docs/baseline-metrics.md).

Install the development distribution in a clean environment and run the
deterministic fixture and tests:

```text
python -m pip install .
python -m arkx.baseline
python -m unittest discover -s tests -t . -v
```

The distribution is currently `codepro==0.3.0.dev0`; it is a packaged
pre-release chassis. The public commands are limited to health and the
deterministic baseline:

```text
codepro --version
codepro doctor --json
codepro baseline
```

There is intentionally no task-submission or executor command yet.

P1 adds deterministic task characterization from explicit signals only. See [the P1 contract](docs/task-characterization.md). It does not select executors or route work.

P2 adds deterministic progress/stagnation assessment from explicit snapshots only. See [the P2 contract](docs/progress-stagnation.md). It does not control execution or authorize retry/replan.

P3 adds bounded rule-based routing and evidence-based escalation decisions. See [the P3 contract](docs/routing-escalation.md). It does not invoke concrete executors.

Block B adds independently removable P4 repository planning/state, P5 patch verification, and P6 handoff/context accounting. P8.2a adds a Treatment A baseline runner and official SWE-bench acceptance adapter; neither owns general orchestration or promotion.

## Checks

The bootstrap check is dependency-free:

```text
python tools/check_foundation.py
```
