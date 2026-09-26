# Agent execution workflow for local repositories

## Purpose

This document governs how the Codepro execution agent works on a local
repository. It addresses workspace state, patches, commits, retries and pull
requests. It does not grant authority to merge, release, promote or erase
unrelated user work.

The policy follows the useful boundary exposed by current agent harnesses:
the task instruction defines the requested outcome, the environment is the
agent's work surface, the verifier decides the task result, and an oracle or
reference solution is a control. A patch, commit or pull request is an output
artifact, not proof that the task is correct.

## Default execution unit

The default unit is:

```text
one task + one workspace/worktree + one attempt identity
```

Before making changes, the agent records:

- workspace path and branch/worktree identity;
- base revision and current `HEAD`;
- pre-existing modified and untracked paths;
- task scope and requested output;
- attempt identity and execution configuration.

The agent must not silently adopt unrelated changes as part of the task. If
the requested change overlaps a pre-existing modification, the attempt is
`BLOCKED` until the overlap is explicitly resolved or the user authorizes the
scope.

## Patch-first delivery

The default delivery is a patch and an evidence record:

```text
task -> inspect -> edit -> focused checks -> full checks when practical
     -> diff/status/evidence -> verification -> acceptance
```

The agent must report at least the changed paths, diff summary, commands run,
observed results, remaining blockers, and the attempt/artifact references.

The agent must not treat any of the following as completion by itself:

- a clean working tree;
- a generated diff;
- a successful local test unrelated to the declared verifier;
- a created commit;
- an open pull request.

## Commit policy

Commits are optional packaging artifacts, not an automatic execution step.
Create one only when the user explicitly requests a commit or the surrounding
workflow has already granted that authority.

When authorized:

1. keep the commit limited to the task scope;
2. inspect the staged file list and diff before committing;
3. run the declared focused checks before the commit;
4. use one task-scoped commit rather than checkpoint commits;
5. record the commit SHA and the evidence revision together.

Never use `git add -A` as a substitute for selecting task files. Never commit
secrets, generated evidence directories, unrelated user changes or an
unverified workaround.

## Retry and continuation policy

A retry is a new attempt, not a new task and not a new pull request. It must:

- receive a new `attempt_id` and verifier `run_id` when its result can differ;
- preserve the previous raw output and failure classification;
- state what changed in the retry configuration or environment;
- avoid overwriting the previous attempt directory;
- reuse the existing task branch/worktree unless isolation was explicitly
  requested.

If a previous attempt is blocked by infrastructure, the next attempt must not
be reported as a task failure or silently switch executor/provider.

## Pull-request policy

Opening or updating a pull request is an explicit external action. It requires
the user to request it or an already-authorized workflow to include it.

Before opening one, the agent must search for an existing branch or PR for the
same task. The default is to update the existing task PR, not create another.
Retries, new verifier runs and additional evidence do not justify duplicate
PRs.

A PR is not ready when the attempt is `BLOCKED`, `FAILED`, `UNKNOWN` or
`NOT_EXECUTED`, unless the PR is explicitly for documenting that failure. A
ready PR record includes:

- task and repository identity;
- base and head revisions;
- changed-file and diff summary;
- focused/full check results and environment limitations;
- verification and independent acceptance state;
- relevant attempt, evidence and commit references.

Merge and promotion remain separate decisions. The execution agent must not
merge its own PR or infer promotion from review availability.

## State crosswalk

```text
EXECUTED + patch       != VERIFIED
VERIFIED               != ACCEPTED
ACCEPTED               != COMMITTED
COMMITTED              != PR_READY
PR_READY               != MERGED
MERGED                 != PROMOTED
```

Each transition needs the evidence and authority declared by the task. Missing
evidence remains missing; it is never filled by the existence of a later Git
artifact.

## External precedent and scope

Harbor's task format separates instruction, environment, tests and optional
oracle solution. SWE-agent documents local patch application separately from
opening a PR, with PR creation as an explicit action. Codepro adopts those
boundaries while adding stricter preservation of user work, attempt lineage,
verification and independent acceptance.