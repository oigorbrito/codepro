# Codepro agent operating rules

The product identity is Codepro. `arkx` is the current Python namespace and
must not be treated as a separate product identity.

## Scope

Treat this repository as an evidence-oriented software-engineering project.
The presence of a module, adapter, test, or document does not prove that the
corresponding capability is qualified for adoption.

## Required implementation standard

Every material capability change must have:

1. an explicit contract or decision record;
2. a falsifiable hypothesis and empirical acceptance criteria;
3. executable tests for deterministic behavior and failure boundaries;
4. recorded raw evidence, including environment and identity where relevant;
5. an independent acceptance decision before promotion.

Local unit-test success is local evidence only. It must not be reported as
upstream, scientific, benchmark, or provider evidence.

## Harness rules

- Preserve provider, model, version, configuration, budget, runtime, and
  treatment identity in every execution record.
- Distinguish identity levels: `experiment_id` identifies the protocol,
  `trial_id` identifies a frozen comparison cell, and `attempt_id` identifies
  one execution attempt. A verifier `run_id` must be unique for every
  control, patch, and retry that can produce a distinct result; it must never
  be reused merely because the task is the same.
- Use stable identity for equivalent frozen protocol inputs, but include the
  control role, patch/diff identity, and attempt semantics wherever a provider
  or verifier can cache results.
- Execute serially when the experiment requires controlled comparison.
- Never silently overwrite an attempt directory or select a fallback executor.
- Persist execution artifacts atomically and keep execution, verification,
  acceptance, and promotion as separate states.
- A qualification record must identify the dataset revision or fingerprint,
  task/base revision, environment image and digest when applicable,
  OS/architecture, executor/provider/model/configuration, verifier identity,
  budget, treatment, control role, and whether the provider was called.
- A provider-free verifier qualification requires both controls: an empty or
  no-op patch must fail as expected and an official gold/oracle patch must
  resolve as expected. A missing control is `NOT_EXECUTED` or `BLOCKED`, never
  a successful qualification.
- Represent missing identity, missing evidence, blocked infrastructure, and
  indeterminate outcomes explicitly; none may become success by inference.
- A failure must retain enough raw output and environment facts to support
  diagnosis and reproducibility.

## Routing and promotion

Route the request before selecting an executor. Simple, localized, and
repository-wide paths are treatment regimes, not implicit executor cascades.
Fallbacks, executor switches, scope expansion, acceptance, and promotion must
be explicit and evidence-backed.

Do not promote a provider, model, executor, or treatment until the declared
authority has accepted the required evidence. A Gold or infrastructure
qualification validates its stated authority and does not by itself prove
mechanism effectiveness or general model quality.

## Agent execution in local repositories

The execution agent is a task worker, not an implicit release manager.

- Start each task by recording the workspace, branch/worktree, base revision,
  and pre-existing working-tree changes.
- Treat one task, one workspace, and one attempt as the default unit. Retries
  receive new attempt identity and preserve the previous artifacts.
- Preserve unrelated local changes. Never use broad `git add -A`, reset, clean,
  checkout, stash, or file deletion to make a workspace look clean unless the
  user explicitly authorizes that exact operation.
- The default deliverable is a verified patch plus evidence. Do not create a
  commit, branch, tag, merge, or pull request unless the request explicitly
  authorizes it.
- When a commit is authorized, make at most the task-scoped commit after the
  declared checks pass. Do not create checkpoint or speculative commits.
- When a pull request is authorized, first locate the task's existing branch
  or open PR and update it when appropriate. Do not create duplicate PRs for
  retries, blocked attempts, or the same task. A blocked, failed, or
  indeterminate attempt is not PR-ready.
- Never infer completion from a clean diff, a created commit, or an open PR.
  Completion requires the declared verification and acceptance evidence.

The complete workspace/patch/commit/PR protocol is in
[`docs/agent-execution-workflow.md`](docs/agent-execution-workflow.md).

## Change discipline

- Preserve unrelated working-tree changes.
- Prefer the smallest change that satisfies the contract.
- Add or update tests with behavioral changes.
- Update the relevant architecture, protocol, or decision documentation when
  the boundary changes.
- Run the focused tests first, then the complete test suite when practical.
- Do not claim merge readiness or a green local baseline while required
  evidence or acceptance records are missing, or while the declared local
  suite is not green. Historical passing runs must retain their revision,
  command, environment, and limitations.

## Documentation status

- Normative rules live in this file and in the current experimental protocol.
- Decision records explain why a boundary exists; they do not silently replace
  the current protocol.
- Logs and manifests are evidence, not policy. A historical log must not be
  presented as the current state without its revision and collection date.
- When a protocol boundary changes, update the protocol, the relevant
  architecture page, and one decision record together. Avoid adding a new
  document when an existing normative contract can be updated.

## Current baseline

The recorded external authority result is `resolved: true` for the official
SWE-bench Docker Gold path on the frozen tasks under `logs/evaluation/`. This
does not qualify a real provider/model or the A/B/C/D mechanism trial.
