# Version Freshness Policy v1

## Purpose

CodePro is evidence-driven. Integration tenure is not evidence that a component remains an appropriate operational candidate.

A pinned historical version can be valuable for reproducibility, but it must not silently remain the current operational candidate after upstream evolution makes that assumption material.

This policy applies to executors, runtime environments, provider clients, local model runtimes, benchmark harnesses, and model families when version identity is available.

## Invariants

```text
LATEST != BEST
OLDER != INVALID
HISTORICAL_CONTROL != CURRENT_CANDIDATE
INTEGRATED != QUALIFIED
UPSTREAM_CHANGE != LOCAL_GAIN
VERSION_GAP != REGRESSION
UNREVIEWED_STALENESS != ACCEPTABLE_DEFAULT
```

## Required identity

For each material external component, record when observable:

- component_id;
- installed_version or pinned_revision;
- source repository or distribution;
- latest_stable_known;
- latest_stable_checked_at;
- version_gap;
- historical_control: true/false;
- current_candidate: true/false;
- qualification_status;
- upgrade_risk;
- relevant upstream changes;
- provenance for the version check.

Unknown fields remain `UNKNOWN`.

## Freshness states

### CURRENT_STABLE

The integrated version matches the latest stable version known at the recorded check time.

This is not evidence that the component is the best choice.

### NEAR_CURRENT

The integrated version is behind, but the observed gap has no known material change relevant to the CodePro execution boundary.

This state requires an explicit recorded comparison of release notes or revisions.

### STALE_REQUIRES_REQUALIFICATION

The integrated version is materially behind and upstream changes may affect capability, reliability, cost, compatibility, execution semantics, or a currently observed blocker.

This state blocks treating the stale version as the sole current operational candidate.

### HISTORICAL_CONTROL_ONLY

The version remains intentionally pinned for reproducibility or comparison, but it is not the current operational candidate.

### VERSION_IDENTITY_UNRESOLVED

The installed binary/distribution cannot be reconciled confidently with an upstream project/release identity.

It must not be classified as current or stale until identity is resolved.

### CURRENT_CANDIDATE_NOT_YET_QUALIFIED

A current stable or otherwise justified candidate has been identified, but CodePro has not yet qualified it under its own protocol.

## Decision rules

1. Do not upgrade solely because a newer release exists.
2. Do not retain an old version solely because it is already integrated.
3. A materially stale current candidate triggers requalification before substantial executor-specific optimization work continues.
4. A historical version may remain frozen as B0/control while a newer candidate is evaluated as C1.
5. Upstream benchmark or release evidence can justify a local hypothesis, never local promotion.
6. Relevant upstream fixes near an observed CodePro blocker increase requalification priority but do not prove the blocker is fixed locally.
7. Version changes are treatment changes and must receive a new treatment/configuration identity.
8. No silent version substitution is permitted during a frozen experiment.
9. Qualification, acceptance, and promotion remain separate decisions.
10. If the exact installed version or distribution is uncertain, use `VERSION_IDENTITY_UNRESOLVED` rather than guessing.

## Freshness review triggers

Perform or refresh the audit:

- before first qualification of an external executor/runtime;
- before starting a new benchmark campaign;
- before investing a new optimization block in a component already classified as materially stale;
- when an observed blocker overlaps with upstream release changes;
- when a major or otherwise material upstream line has appeared;
- when treatment identity is being re-frozen after a long-lived experiment.

A freshness review is observational. It does not itself authorize an upgrade or promotion.

## Minimal comparison pattern

When a material gap exists:

```text
B0 = currently integrated/pinned version
C1 = current stable candidate at an exact pin
```

First test compatibility and runtime behavior. Quality/cost comparisons are only meaningful after both cells can produce comparable, verifiable runs.

A candidate that cannot satisfy the frozen execution/evidence contract is not promoted merely because it is newer.

## Documentation rule

Every qualification or experiment involving an external executable component must make its freshness state visible in the evidence artifact or treatment manifest.

The project contract remains authoritative when this policy conflicts with convenience.
