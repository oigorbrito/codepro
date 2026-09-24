# ADR 0023 — Read-only project inspection CLI

## Status

Accepted for empirical validation.

## Observed need

The CodePro CLI could be installed and could report help/version/runtime health, but it could not yet describe the project it was being asked to operate on.

The intended CLI workflow requires project context before executor invocation is even considered. That need can be tested without introducing orchestration or agent execution.

## Decision

Add a read-only `codepro inspect` command.

The command may observe:

- requested project directory;
- Git executable availability;
- Git repository root and current branch/detached HEAD;
- language markers at the project root;
- conventional test-surface directories;
- availability of known executor binaries on PATH: `codex`, `claude`, and `gemini`.

It must not:

- invoke an executor;
- choose/rank an executor;
- run project tests;
- modify Git state;
- write configuration;
- alter files;
- infer that an available binary is healthy or authenticated.

`--json` exposes the same observation as deterministic machine-readable output.

## Empirical acceptance

The capability is acceptable only if:

1. non-Git directories remain inspectable;
2. missing project paths fail closed;
3. language-marker ordering is deterministic;
4. executor availability is reported as availability only;
5. the real repository can be inspected in CI;
6. the complete CodePro suite remains green on Python 3.12, 3.13, and 3.14;
7. the chassis semantic fingerprint remains unchanged;
8. mutation sensitivity remains unchanged.

## Alternatives

- Auto-run detected tests: rejected because detection does not establish permission or the correct test command.
- Auto-select an available executor: rejected because binary presence is not executor qualification.
- Add an interactive task prompt in the same change: rejected because project inspection and task execution are independently falsifiable capabilities.

## Removal condition

Remove or replace this component if its observations are not used by a later validated workflow, or if a simpler mechanism provides the same deterministic project context with lower maintenance cost.
