# AGENTS.md

These instructions apply to `experiments/integrations/minisweagent/` and override broader repository guidance when more specific.

## Purpose

This directory exists to reproduce and qualify the pinned mini-SWE-agent SWE-bench reference path. It is an experimental integration boundary, not product runtime.

## Pinned reference

- repository: `SWE-agent/mini-swe-agent`
- version: `v2.4.6`
- commit: `a83fcae82d2a08f0ee0c688f9d137b3566c097f8`
- bundled SWE-bench config blob: `106decd160e72e5164e29d15d23da354c29c309d`

Do not silently update these references.

## Baseline rules

- Import and exercise upstream runner/environment functions directly where practical.
- Do not copy upstream behavior into a custom CodePro implementation merely for convenience.
- Do not fall back to LocalEnvironment, Git Bash, MSYS2, SWE-ReX, Modal or another backend.
- Do not enable CodePro routing, recovery, compaction, replanning, handoff or executor switching.
- Do not call a model/provider until provider-free qualification and verifier controls pass.
- Do not patch mini-swe-agent to make a baseline pass.
- Do not change the task, dataset revision, prompt, retry policy, timeout policy or verifier without recording a protocol deviation/new treatment.

## Provider-free task state

For SWE-bench task images:

- derive the image through upstream mini logic;
- instantiate through upstream `get_sb_environment()`;
- require `/testbed`, Linux and the configured shell/environment;
- require the task `base_commit` to be an ancestor of the prepared HEAD;
- require the initial worktree to be clean;
- record the prepared HEAD and commits after the base commit;
- do not require prepared HEAD equality with the base commit.

A non-ancestor base commit or dirty initial worktree is a material provenance failure.

## Workload and image provenance

Record:

- dataset repository, subset and split;
- dataset revision when available, otherwise dataset fingerprint;
- instance ID and base commit;
- problem statement/content hash when used in a frozen study;
- image name plus resolved digest/ID;
- prepared HEAD and preparation commits;
- architecture and OS.

A mutable image tag alone is insufficient provenance.

## Verifier

SWE-bench official evaluation is authoritative for benchmark resolution.

- Negative controls, gold/positive controls and agent predictions use unique `run_id` values.
- Never reuse a run ID after changing a prediction diff.
- CodePro local patch checks are not substitutes for SWE-bench `resolved`.
- Preserve verifier repository/version, dataset identity, instance ID and output artifacts.

## Experimental comparisons

After the reference baseline is demonstrated, alternative substrates or mechanisms are treatments.

For each treatment:

- keep workload/model/provider/verifier fixed unless that field is the manipulated variable;
- change one behavior-affecting variable at a time initially;
- measure official resolution, tokens, cost, provider calls, wall time, retries, timeouts and failure classes;
- preserve failures and blocked states as evidence.

## Required validation

When modifying this integration:

- run the focused tests under `tests/test_minisweagent_*.py`;
- run `git diff --check`;
- keep `provider_called = false` for infrastructure-only changes;
- update the relevant ADR/addendum when an invariant changes;
- preserve the frozen historical audit rather than rewriting past observations.
