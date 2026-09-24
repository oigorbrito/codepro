# ADR 0011 — Freeze workload membership and selection rules

## Status

Accepted for the Arkx empirical chassis.

## Observed need

Study Spec v1 references a workload but does not define the workload itself. A mutable task list permits silent task substitution, treatment-specific filtering, or changes in ordering that can undermine fair comparison and replication.

## Decision

Add Workload Manifest v1. It freezes source/version, target population, sampling strategy, selection rationale, inclusion/exclusion criteria, exact task membership, holdout policy, task order, and seeds when randomness is used.

## Alternatives considered

- Put all task IDs directly in Study Spec: rejected because large workloads should remain independently reusable and content-addressable.
- Trust benchmark defaults without a manifest: rejected because benchmark versions and selected subsets can change.
- Permit task replacement after execution starts: rejected unless recorded explicitly as a protocol deviation.

## Limitation

The manifest guarantees explicit reproducible selection, not real-world representativeness. External and construct validity remain separate study obligations.

## Rollback/removal condition

Replace this contract if a benchmark-native immutable manifest provides equivalent fields and Arkx records its immutable identity without loss.
