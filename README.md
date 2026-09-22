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

## Checks

The bootstrap check is dependency-free:

```text
python tools/check_foundation.py
```

