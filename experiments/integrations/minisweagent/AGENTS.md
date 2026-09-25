# mini-SWE-agent reference integration rules

Read the repository root `AGENTS.md` first. These rules apply only to
`experiments/integrations/minisweagent/`.

## Frozen reference

- mini-swe-agent: `v2.4.6`
- commit: `a83fcae82d2a08f0ee0c688f9d137b3566c097f8`
- SWE-bench config Git blob: `106decd160e72e5164e29d15d23da354c29c309d`

Do not update these references silently.

## Baseline

- import upstream environment/config/runner behavior; do not reimplement it;
- baseline substrate is Docker/Linux and `/testbed`;
- no fallback to local/Git-Bash/MSYS2/SWE-ReX/Modal/Harbor;
- do not alter task, prompt, timeout, retry, verifier or backend to obtain PASS;
- no model/provider call before provider-free qualification;
- CodePro routing/recovery/compaction/replanning/handoff remain outside baseline.

## Prepared repository state

Require:

```text
base_commit is ancestor of prepared HEAD
AND initial working tree is clean
```

Record prepared HEAD and commits ahead. Do not require HEAD equality.

## Evidence

A new integration rule needs a Decision Basis under the root policy.
Provider-free PASS is infrastructure evidence only.
