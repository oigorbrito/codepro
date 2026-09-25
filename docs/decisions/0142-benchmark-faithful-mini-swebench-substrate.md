# ADR 0142 — Restore the benchmarked mini-SWE-agent SWE-bench substrate

## Status

Accepted for provider-free qualification implementation. Not promoted.

## Context

Earlier qualification work used mini-SWE-agent v2.4.6 at commit
`a83fcae82d2a08f0ee0c688f9d137b3566c097f8`, but an experimental execution
path substituted a host-local Windows/Git-Bash boundary for the environment
encoded by mini-SWE-agent's bundled SWE-bench configuration.

That substitution is material. At the pinned commit, the bundled
`src/minisweagent/config/benchmarks/swebench.yaml` specifies:

- `environment_class: docker`;
- `cwd: /testbed`;
- `interpreter: ["bash", "-c"]`;
- `BASH_ENV: /root/.bashrc`;
- per-command timeout of 60 seconds.

The failed local path was:

`CodePro -> mini-SWE-agent -> host-local Bash -> Git Bash/MSYS2 -> Windows`.

That path is not the benchmark reference substrate.

## Decision

Restore the upstream execution substrate before any model/provider qualification:

```text
CodePro qualification boundary
        |
        v
mini-SWE-agent v2.4.6 @ a83fcae...
        |
        v
bundled SWE-bench configuration
        |
        v
Docker/Linux instance environment
        |
        v
/testbed + bash -c + BASH_ENV
        |
        v
provider-free observations
```

The implementation MUST fail closed if Docker is unavailable. It MUST NOT
fallback to LocalEnvironment, Git Bash, MSYS2, SWE-ReX, Modal, Harbor, or any
other backend without a new explicit decision.

## Decision basis

```text
problem_class = benchmark substrate fidelity
decision = use the exact upstream SWE-bench Docker substrate
basis_type = UPSTREAM_IMPL + OFFICIAL_DOC
basis_ref =
  SWE-agent/mini-swe-agent v2.4.6
  commit a83fcae82d2a08f0ee0c688f9d137b3566c097f8
supported_claim =
  the reference SWE-bench profile uses Docker/Linux, /testbed, bash -c,
  BASH_ENV=/root/.bashrc
applicability =
  Issue #36 qualification must reproduce the reference substrate before
  comparing runtime behavior
deviation = none
```

## Preserved CodePro boundaries

This does not make mini-SWE-agent a core dependency and does not promote it.

```text
AVAILABILITY != QUALIFICATION
EXECUTION != VERIFICATION
VERIFICATION != ACCEPTANCE
ACCEPTED != PROMOTED
NO_SILENT_FALLBACK
NO_SILENT_EXECUTOR_SWITCH
```

## Provider-free acceptance criteria

Before any provider/model call:

1. verify exact mini-SWE-agent commit;
2. verify a clean mini worktree;
3. verify the bundled SWE-bench config identity;
4. verify Docker CLI and daemon access;
5. optionally execute a minimal Linux container probe;
6. instantiate the task environment through upstream mini-SWE-agent;
7. record commands, versions, stdout/stderr, exit status, image identity and cleanup.

Passing these checks is infrastructure compatibility evidence only.

## References

- https://github.com/SWE-agent/mini-swe-agent/releases/tag/v2.4.6
- https://github.com/SWE-agent/mini-swe-agent/blob/a83fcae82d2a08f0ee0c688f9d137b3566c097f8/src/minisweagent/config/benchmarks/swebench.yaml
- https://github.com/SWE-agent/mini-swe-agent/blob/a83fcae82d2a08f0ee0c688f9d137b3566c097f8/src/minisweagent/run/benchmarks/swebench_single.py
