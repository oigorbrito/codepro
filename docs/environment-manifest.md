# Environment Manifest v1

The Environment Manifest records the execution facts required to reproduce or audit a run without overstating how controlled the environment really was.

## Current foundation posture

CodePro foundation CI pins:

- Ubuntu runner label `ubuntu-24.04`;
- CPython `3.14.7`;
- GitHub Actions by immutable commit SHA.

The CI fingerprint also records the actual hosted runner image version, architecture, locale/timezone signal, platform, and CodePro commit.

The hosted runner remains **non-hermetic** because `ubuntu-24.04` selects a GitHub-managed image whose exact build is observed at run time rather than selected by an immutable container digest.

## Dependency and container semantics

If no dependency lock exists, the manifest requires an explicit justification. The current foundation is standard-library-only, so absence of a third-party dependency lock is deliberate rather than silently missing.

If no immutable container digest is used, the manifest also requires justification. Non-container execution must not be described as hermetic.

## Boundary

```text
PINNED_LANGUAGE_RUNTIME != HERMETIC_ENVIRONMENT
RECORDED_RUNNER_IMAGE != IMMUTABLY_SELECTED_IMAGE
ENVIRONMENT_FINGERPRINT != FULL_MACHINE_RECONSTRUCTION
NO_THIRD_PARTY_DEPENDENCIES != MISSING_LOCKFILE
```
