# CodePro

CodePro is an evidence-oriented software-engineering chassis for building,
qualifying, and comparing execution mechanisms without collapsing local success
into benchmark or product claims.

The public product identity is **CodePro**. The Python import namespace remains
`arkx` temporarily for compatibility.

> **MINIMUM SUFFICIENT ARCHITECTURE**  
> **FOR MAXIMUM RELIABLE CAPABILITY**

This repository is the canonical project root.

## What lives here

CodePro currently contains:

- explicit project and evidence invariants;
- deterministic execution, verification, recovery, acceptance, and promotion
  boundaries;
- an experimental harness and reproducibility contracts;
- executor/provider qualification records and treatment definitions;
- repository planning, routing, handoff, and telemetry mechanisms;
- an auditable agent workflow for local repository work;
- tests and structural checks for the local contracts.

The presence of a component does **not** mean that it is benchmark-proven,
accepted, or promoted.

## Current qualification state

The current qualification lineage distinguishes historical results from the
latest provider-free reference work.

```text
Qualification Run v1 = BLOCKED
REFERENCE_PROVIDER_FREE_PATH_READY
promotion = NOT_AUTHORIZED
```

The provider-free path qualifies the declared environment/verifier path only.
It does not by itself qualify a provider, model, executor treatment, or product
release.

Provider/model execution and behavior-changing CodePro treatments remain
separate qualification steps.

## Evidence model

CodePro keeps these states distinct:

```text
HYPOTHESIS != IMPLEMENTATION
IMPLEMENTATION != EXECUTED
EXECUTED != VERIFIED
VERIFIED != ACCEPTED
ACCEPTED != PROMOTED

BLOCKED != PASS
NOT_EXECUTED != PASS
LOCAL_PASS != BENCHMARK_RESULT
```

Experimental work uses explicit identity levels:

```text
experiment_id
trial_id
attempt_id
verifier_run_id
```

Distinct controls, patches, and retries must not reuse a verifier run ID when
they can produce different results.

Qualification records must preserve the relevant dataset revision/fingerprint,
task/base revision, environment image/digest, OS/architecture,
executor/provider/model/configuration, verifier identity, treatment, control
role, and whether the provider was called.

A machine-readable manifest indexes raw evidence; it does not replace logs,
diffs, trajectories, verifier output, or environment captures.

See:

- [project contract](docs/project-contract.md)
- [experimental protocol](docs/experimental-protocol.md)
- [architecture boundary](docs/architecture.md)
- [qualification identity and controls](docs/decisions/0146-qualification-identity-and-controls.md)

## Agent execution workflow

Repository work is patch-first by default:

```text
task
-> inspect workspace
-> edit
-> focused checks
-> broader checks when practical
-> diff/status/evidence
-> verification
-> acceptance
```

The default execution unit is one task, one workspace/worktree, and one attempt
identity. Retries receive new attempt identity and preserve prior evidence.

Commits and pull requests are explicit authorized actions, not automatic
consequences of editing or passing a local test. A retry does not create a new
PR by default; an existing task PR should be updated when PR work is authorized.

The agent must preserve pre-existing user changes and must not use broad
`git add -A`, reset, clean, checkout, stash, or destructive deletion merely to
make a workspace appear clean.

```text
patch != verified
commit != verified
PR != accepted
merged != promoted
```

See the full [agent execution workflow](docs/agent-execution-workflow.md) and
[ADR 0147](docs/decisions/0147-agent-local-workspace-and-pr-policy.md).

## Development posture

New architecture is justified by observed need and evidence, not by component
tenure or preference.

No fallback, executor switch, scope expansion, benchmark reinterpretation, or
promotion may happen silently.

Local tests are local evidence. A non-green local suite must not be described as
a green baseline, and historical passing runs must retain their revision,
command, environment, and limitations.

Operational instructions for agents live in [AGENTS.md](AGENTS.md). Decision
records explain why a boundary exists; logs and manifests are evidence, not
policy.

## Install and use

### Requirements

At a high level, using CodePro currently means working from a checked-out
repository with a supported Python environment. Some experimental qualification
paths also require their own external runtime, such as Docker, but those are not
part of the minimal CLI installation.

### Install from the repository

From the repository root:

```text
python -m pip install .
```

For development, install the current checkout in editable form:

```text
python -m pip install -e .
```

Confirm the installed command:

```text
codepro --version
codepro doctor --json
```

### Use CodePro at the current product boundary

The public CLI currently exposes project health and deterministic baseline
operations:

```text
codepro doctor --json
codepro baseline
```

At a high level:

1. use `codepro doctor --json` to inspect whether the local installation and
   basic environment are usable;
2. use `codepro baseline` to execute the deterministic CodePro baseline;
3. use the repository's `experiments/`, harnesses, and documented protocols
   for qualification or benchmark work;
4. treat produced patches, logs, manifests, verifier output, and other artifacts
   as evidence governed by the project protocol;
5. do not infer acceptance or promotion from a local command completing
   successfully.

CodePro does **not** currently expose a general-purpose command that accepts an
arbitrary software task and autonomously selects/runs a production executor.
Executor/provider qualification and benchmark integrations remain explicit
experimental workflows.

For repository work performed by an agent, follow
[AGENTS.md](AGENTS.md) and the
[agent execution workflow](docs/agent-execution-workflow.md).

## CLI

Install the current checkout:

```text
python -m pip install .
```

Current public commands include:

```text
codepro --version
codepro doctor --json
codepro baseline
```

The equivalent Python namespace remains `arkx` while compatibility is
preserved.

## Local checks

Run the deterministic foundation check:

```text
python tools/check_foundation.py
```

Run the baseline and local suite when the task requires them:

```text
python -m arkx.baseline
python -m unittest discover -s tests -t . -v
```

Record the actual result. Do not infer verification, acceptance, benchmark
success, or merge readiness from command execution alone.

## Repository map

```text
AGENTS.md      agent operating rules
docs/          contracts, architecture, protocol, decisions
experiments/   experimental fixtures and qualification artifacts
src/           product/runtime contracts and mechanisms
tests/         executable local verification boundary
tools/         repository and experiment utilities
logs/          recorded evidence; not normative policy
```
