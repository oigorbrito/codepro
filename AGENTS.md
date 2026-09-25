# AGENTS.md

## Product identity

- The canonical product/project name is **CodePro**.
- The internal Python namespace `arkx` is legacy and remains temporarily for compatibility. Do not introduce new public/docs/worktree names using Arkx unless documenting history.
- Do not rename frozen schema/provenance identities without an explicit migration decision.

## Engineering contract

- Prefer the minimum sufficient architecture for the observed need.
- Do not grant tenure to a component merely because it exists.
- Preserve these invariants:
  - `SCIENTIFIC_SIGNAL != LOCAL_PASS`
  - `UPSTREAM_EVIDENCE != LOCAL_EVIDENCE`
  - `IMPLEMENTATION != EXECUTED`
  - `EXECUTED != ACCEPTED`
  - `ACCEPTED != PROMOTED`
  - `BLOCKED != PASS`
  - `NOT_EXECUTED != PASS`
  - `NO_SILENT_FALLBACK`
  - `NO_SILENT_EXECUTOR_SWITCH`
  - `NO_SILENT_SCOPE_EXPANSION`

## Benchmark and empirical-work rules

When work is motivated by a benchmark, paper, donor implementation, published result, or external experiment:

1. Identify the exact upstream repository, commit/version, configuration, workload, model/provider and verifier when available.
2. Reproduce the reference path before optimizing or adapting it.
3. Do not substitute a merely supported backend for the backend used by the reference result.
4. Preserve benchmark-material semantics: environment, runner, prompt/tool contract, retry/timeout policy, patch extraction and verifier.
5. Record deviations explicitly. A behavior-changing deviation is a treatment, not a baseline repair.
6. Change one behavior-affecting variable at a time in comparative experiments.
7. Report quality together with cost/tokens, provider calls, wall time, retries, timeouts and failure classes when relevant.
8. Treat smoke tests, synthetic fixtures and local passes as local evidence only.
9. Official benchmark claims must come from the benchmark's authoritative verifier/harness.
10. Do not promote architecture from a mechanism pass alone.

## Reproducibility

For empirical runs, record immutable identity wherever possible:

- CodePro commit;
- executor/agent commit and version;
- config Git blob/hash;
- dataset repository/subset/split and revision or fingerprint;
- instance/task identity and base revision;
- container image digest/ID, not only a mutable tag;
- model/provider and effective settings;
- environment/OS/architecture;
- verifier/harness version;
- commands, exit codes and evidence artifacts.

If a mutable reference such as `:latest` is required by an upstream runner, record the resolved immutable digest/ID as evidence.

## SWE-bench / mini-SWE-agent baseline

For the current mini-SWE-agent qualification lineage:

- reference mini: `v2.4.6` at `a83fcae82d2a08f0ee0c688f9d137b3566c097f8`;
- reference config blob: `106decd160e72e5164e29d15d23da354c29c309d`;
- use the upstream SWE-bench runner/environment path rather than a CodePro reimplementation;
- the provider-free baseline must pass before model/provider execution;
- CodePro routing, recovery, compaction, replanning, handoff and silent fallback are disabled in the reference baseline;
- SWE-ReX, Modal, Harbor or other substrates are explicit treatments/comparators unless evidence proves they are the historical reference path;
- official SWE-bench evaluation is authoritative for `resolved`.

For a prepared SWE-bench repository, do **not** require `HEAD == instance.base_commit`. Validate that the base commit is an ancestor of the prepared HEAD, the initial worktree is clean, and record any preparation commits as provenance.

Use a unique SWE-bench verifier `run_id` for every distinct prediction/control. Result caching is keyed by run ID and instance and can otherwise reuse stale evidence.

## Historical qualification state

Do not rewrite historical evidence:

- `Qualification Run v1 = BLOCKED`;
- `promotion = NOT_AUTHORIZED`.

A later successful run starts or advances a new qualification lineage; it does not relabel v1.

## Validation before commit

For changes affecting benchmark/runtime behavior:

- run focused regression tests for the changed invariant;
- run `git diff --check`;
- validate JSON artifacts if modified;
- preserve provider-free gates when the change is infrastructure-only;
- do not interpret CI failure without logs as a code regression.

## Relevant documentation

Use these files when the task touches their subject:

- `docs/project-contract.md` for project invariants and product boundaries;
- `docs/benchmark-fidelity-audit.md` for benchmark-fidelity policy;
- `docs/benchmark-fidelity-audit-v2-addendum.md` for the prepared-repo-state correction;
- `docs/decisions/0142-benchmark-faithful-mini-swebench-substrate.md` for the pinned mini Docker baseline;
- `docs/decisions/0143-swebench-prepared-repo-state.md` for SWE-bench repository-state semantics;
- `experiments/integrations/minisweagent/AGENTS.md` for mini/SWE-bench-specific execution rules.
