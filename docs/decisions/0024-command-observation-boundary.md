# ADR 0024 — Command observation before executor semantics

## Status

Accepted for empirical validation.

## Context

CodePro needs a runtime boundary before Codex, Claude Code, Gemini CLI, or any other executor can be integrated safely.

Software-engineering agent harnesses converge on a useful separation:

- an environment executes commands and records process outcomes;
- non-zero exit is not automatically a task failure;
- timeout is represented separately;
- environment/launch failure is distinct from command exit;
- higher layers decide whether an observation means reproduce, continue, retry, block, verify, or fail.

Relevant implementation references reviewed:

- mini-SWE-agent local environment:
  https://github.com/SWE-agent/mini-swe-agent/blob/main/src/minisweagent/environments/local.py
- OpenHands workspace command result:
  https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/workspace/models.py
- OpenHands workspace execution boundary:
  https://github.com/OpenHands/software-agent-sdk/blob/main/openhands-sdk/openhands/sdk/workspace/base.py
- SWE-agent environment command-check semantics:
  https://github.com/SWE-agent/SWE-agent/blob/main/sweagent/environment/swe_env.py

These references motivate falsifiable properties; they are not dependencies.

## Decision

Introduce a minimal command observation boundary:

- `CommandSpec`
  - explicit argv tuple;
  - explicit cwd;
  - finite positive timeout;
  - explicit `INHERIT_PROCESS` environment policy for schema v1;
  - no implicit shell.

- `CommandResult`
  - argv;
  - resolved cwd;
  - exit code when a process was launched;
  - stdout;
  - stderr;
  - timeout flag;
  - duration;
  - explicit environment error.

- `CommandEnvironment` protocol.

- `LocalCommandEnvironment`
  - one fresh process per command;
  - direct argv execution with `shell=False`;
  - separate stdout/stderr capture;
  - process-group/session isolation where supported;
  - timeout attempts to terminate the complete child process group;
  - timeout cleanup is itself bounded, avoiding an unbounded post-timeout `communicate()` wait.

## Normative invariants

```text
NONZERO_EXIT != TASK_FAILURE
TIMEOUT != NONZERO_EXIT
ENVIRONMENT_ERROR != COMMAND_EXIT
COMMAND_OBSERVATION != VERIFICATION
EXECUTION != ACCEPTANCE
BINARY_AVAILABLE != EXECUTOR_QUALIFIED
```

The command module must not import or emit `ExecutionStatus`.

## Empirical acceptance

Tests must demonstrate:

1. zero exit with separate stdout/stderr;
2. non-zero exit remains an observation with no status field;
3. cwd is explicit and recorded;
4. argv metacharacters are not shell-interpreted;
5. missing executable becomes an environment error;
6. missing cwd becomes an environment error;
7. timeout is distinct from non-zero exit;
8. POSIX timeout kills child processes in the command process group;
9. serialization is deterministic and round-trips;
10. environment inheritance is explicit in the serialized spec;
11. the repository CI can deliberately observe exit code 7 while the observation probe itself remains valid;
12. existing mutation, property, metamorphic, fingerprint, and cross-Python checks remain green.

## Non-goals

- executor registry;
- executor qualification;
- provider/model selection;
- task-status inference;
- retry policy;
- verification;
- acceptance;
- promotion;
- TUI.

These belong to later issues.

## Removal condition

Remove or replace this boundary if a simpler implementation preserves the same observable distinctions, process cleanup guarantees, and executor independence.
