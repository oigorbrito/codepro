# ADR 0142 — Restore the benchmarked mini-SWE-agent SWE-bench substrate

## Status

Accepted for implementation on an experimental branch. Not promoted.

## Context

Qualification experiments used mini-SWE-agent v2.4.6 at commit
`a83fcae82d2a08f0ee0c688f9d137b3566c097f8`, but the experimental execution
path substituted a host-local Windows/Git-Bash boundary for the environment used
by mini-SWE-agent's bundled SWE-bench configuration.

That substitution is material. At the pinned commit, the bundled
`src/minisweagent/config/benchmarks/swebench.yaml` specifies:

- `environment_class: docker`;
- `cwd: /testbed`;
- `interpreter: ["bash", "-c"]`;
- `BASH_ENV: /root/.bashrc`;
- a per-command timeout of 60 seconds.

The pinned SWE-bench runner also defaults an unspecified environment class to
`docker`, derives the official SWE-bench image for each instance, and injects
that image into the environment.

The failed local path was instead:

`CodePro -> mini-SWE-agent -> host-local Bash -> Git Bash/MSYS2 -> Windows`.

That path is not the substrate encoded by the benchmark configuration and is
therefore not a faithful reproduction of the benchmarked execution architecture.

## Evidence

Primary reference, pinned to the exact mini-SWE-agent revision used by the
qualification experiment:

- `SWE-agent/mini-swe-agent@a83fcae82d2a08f0ee0c688f9d137b3566c097f8`
- `src/minisweagent/config/benchmarks/swebench.yaml`
- `src/minisweagent/run/benchmarks/swebench.py`

Additional external evidence reviewed before this decision:

- SWE-bench experiment submissions include regular mini-SWE-agent benchmark runs,
  historically labelled "bash-only".
- The "bash-only" label describes the agent/tool interface; it does not imply
  Git Bash on a Windows host.
- mini-SWE-agent also supports SWE-ReX Docker/Modal environments, but those are
  not required to restore the pinned SWE-bench baseline.

## Decision

Restore the benchmark reference architecture before adding CodePro-specific
optimizations:

```text
CodePro experiment boundary
        |
        v
mini-SWE-agent v2.4.6 @ a83f...
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
patch / predictions
        |
        v
independent SWE-bench verifier
```

The implementation MUST fail closed if Docker is unavailable. It MUST NOT fall
back to `LocalEnvironment`, Git Bash, MSYS2, SWE-ReX, Modal, or another backend
without a new explicit protocol/architecture decision.

The first restored run is infrastructure qualification, not a promotion event.

## Preserved CodePro boundaries

This decision does not make mini-SWE-agent a core dependency. The integration
remains outside `src/arkx` until benchmark evidence justifies promotion.

The existing CodePro contracts remain authoritative:

- availability != qualification;
- execution != verification;
- verification != acceptance;
- accepted != promoted;
- no silent fallback;
- no silent executor switch;
- configuration changes are protocol deviations.

## Qualification lineage

The existing Qualification Run v1 remains historical evidence:

- Gate A = PASS
- Gate B = BLOCKED
- verifier = NOT_EXECUTED
- promotion = NOT_AUTHORIZED
- Qualification Run v1 = BLOCKED

The corrected substrate must use a new qualification lineage. It must not rewrite
or relabel v1.

## Acceptance criteria for the corrected substrate

Before any provider/model call:

1. verify the mini repository is exactly at the pinned commit;
2. verify the bundled SWE-bench config is present and still selects Docker;
3. verify Docker CLI and daemon access;
4. execute a minimal Linux container probe successfully;
5. execute the mini SWE-bench command far enough to demonstrate configuration
   resolution without silently selecting a different environment;
6. record commands, versions, stdout/stderr, exit codes and image identity.

Only after those provider-free checks pass may a bounded qualification run be
considered.

## Removal condition

Remove this integration if a closer, better-evidenced benchmark reference
replaces it, or if upstream benchmark methodology changes and the change is
documented with equivalent reproducibility evidence.
