# ADR 0090: P8.2 baseline adapter adopts canonical configuration snapshots

## Status

Accepted for local architectural evidence; P8.2 remains experiment-coupled.

## Decision

`BaselineRunConfig.configuration_snapshot()` is the canonical source for the
existing P8.2 `identity_digest()`. The preflight identity and capability digest
use the same snapshot digest. The snapshot contains the existing frozen public
configuration fields and no secret material.

## Falsifiable hypothesis and acceptance criteria

H1: P8.2 preflight and configuration identity cannot drift because they derive
from one canonical snapshot. Tests must prove digest equality and secret-safe
serialization.

## Consequences

This is an adoption step, not a qualification result. It does not make
minisweagent available, qualify a provider/model, or generalize the P8.2
treatment into a universal executor.
