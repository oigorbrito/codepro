# 0037 — Second Executor Enablement

## Status

`BLOCKED`: a qualification paired run cannot start until a second concrete
executor is available and independently identified.

## Decision

The next work item is infrastructure enablement, not routing, composition,
fallback, ranking, or another qualification abstraction. The project must make
one additional task-solving executor runnable through the existing neutral
contract and verifier.

Changing the Ollama model, provider, or runtime does not satisfy this decision
when the task is still executed by the same `mini-swe-agent` implementation.
Those are treatment/provider variables and must remain labeled as such.

## Falsifiable hypothesis

An independently implemented executor can execute the same frozen task,
revision, acceptance definition, budget, verifier, and instrumentation as the
existing executor, without executor-specific branches or hidden fallback.

## Required enablement evidence

The second executor is not enabled until all of the following are recorded:

1. stable executor identity, implementation/version, configuration digest, and
   runtime identity;
2. headless invocation with a bounded timeout and explicit exit status;
3. extracted patch/artefact and raw stdout/stderr;
4. observable budget, calls/tokens where supported, and wall time;
5. the same verifier and acceptance boundary used by executor one;
6. an isolated smoke task that proves the complete execution → verification →
   acceptance path;
7. no fallback, executor switch, or executor-specific treatment branch;
8. independent acceptance of the preflight evidence.

## Current preflight

The latest read-only collection found:

- `mini-swe-agent`: installed and usable as the existing P82 execution path;
- Ollama `0.34.3`: available as a provider/runtime only; not a second
  executor;
- Git Bash: `BLOCKED` by executable/access failure;
- Docker `29.7.2`: CLI present, daemon access `BLOCKED` by permission denied;
- OpenRouter boundary: `UNKNOWN` because provider/configuration identity is not
  frozen for the current run.

Additional installed candidates were checked on 2026-09-24. Claude Code was
blocked by missing login, OpenCode was blocked while spawning its server, and
Aider was blocked by local application-control policy. Codex was not counted
because it is the controlling agent, not an independent comparator. Raw output
is preserved in
`logs/architecture/second-executor-preflight-20260924.json`; the attempted
qualification is recorded as `BLOCKED` in
`logs/qualification/executor-qualification-v1-20260924.json`.

The dedicated OpenCode audit found version `2.0.15`, a documented headless
`run` entrypoint, model syntax `provider/model#variant`, and JSON output via
`--format json`. However, the installed CLI rejects `--standalone` when used
with `run`, while the default and isolated invocations fail before execution
with `EPERM`. Detailed observations are preserved in
`logs/architecture/opencode-headless-audit-20260924.json`.

These observations are infrastructure evidence. They do not qualify a second
executor and do not authorize a paired benchmark.

## Exit criteria

When the evidence above exists, run `Executor Qualification v1` unchanged:
same frozen task set, revisions, verifier, instrumentation, budget,
replicates, and serial order. Only after that run produces complete comparable
cells may `Baseline v1` begin. Routing remains out of scope until then.
