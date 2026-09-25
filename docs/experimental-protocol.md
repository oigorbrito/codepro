# Experimental protocol

Codepro develops through empirical increments. The protocol below defines the
minimum record required before a capability can be considered for promotion.

## Required record

Each experiment records:

- `id`: stable identifier;
- `hypothesis`: falsifiable statement;
- `scope`: exact systems, inputs, and exclusions;
- `implementation`: what changed, if anything;
- `executor`: the exact executor and version/configuration;
- `identity`: resolved dataset revision or fingerprint, task IDs and base
  revisions, environment image/digest and OS/architecture when applicable,
  verifier identity, provider/model identity, and Codepro/runner revision;
- `attempts`: explicit `experiment_id`, `trial_id`, `attempt_id`, and verifier
  `run_id` values. Equivalent frozen trials may share a stable trial identity,
  but distinct patches, controls, or retries must not reuse a verifier run ID;
- `procedure`: reproducible steps;
- `expected_signal`: measurable success and failure criteria;
- `controls`: declared negative/no-op and positive/gold controls, with their
  expected states and raw evidence paths;
- `result`: `PASS`, `FAIL`, `BLOCKED`, or `NOT_EXECUTED`;
- `evidence`: links or paths to raw evidence and environment facts;
- `provider_called`: explicit boolean or `UNKNOWN` when it cannot be
  established;
- `acceptance`: explicit reviewer decision and rationale;
- `promotion`: explicit decision to make the change durable, or `NOT_PROMOTED`.

The experiment record is the canonical machine-readable index for these
facts. It must reference raw logs, diffs, trajectories, verifier output and
environment captures; it does not replace them. Missing identity or missing
raw evidence makes the relevant claim `BLOCKED`, `UNKNOWN`, or
`NOT_EXECUTED`, according to the declared protocol.

## Identity and verifier controls

Use four identity levels:

```text
experiment_id  = protocol and scope
trial_id       = frozen comparison cell
attempt_id     = one execution attempt
verifier_run_id = one verifier cache namespace for one control/patch attempt
```

For provider-free verifier qualification, execute the controls serially with
the same task, base revision, environment and verifier:

```text
no-op/empty patch  -> expected failure
gold/oracle patch  -> expected resolution
candidate patch    -> observed result, if a candidate exists
```

The gold control qualifies only the stated verifier/environment authority. It
does not qualify a provider, model, agent, treatment, or general task-solving
capability.

P7 composition trials use their own comparability namespace: `COMPARABLE`, `INCOMPARABLE`, and `UNKNOWN`. P7 records externally supplied measurements and does not convert them into acceptance results.

P8.1 adds executor qualification records with explicit `EXECUTOR` and `TREATMENT` comparison axes. P8.1 records externally supplied execution outcomes and acceptance observations; it does not execute an executor, infer acceptance, rank executors, or promote components.

P8.2 defines the minimal mechanism trial as a declarative A/B/C/D plan over a
fixed executor: baseline, safe editor, enhanced repository context, and their
combination. Its harness freezes task, replicate, executor, model,
environment, budget, verification, and independent acceptance authority. It
does not invoke an executor or mechanism and does not manufacture acceptance;
results remain P8.1 observations. Missing controls and measurements remain
`UNKNOWN`, and the only intended treatment difference is the declared arm.

P8.2a adds the Treatment A baseline runner. Each attempt is serial, refuses to
overwrite an existing attempt directory, derives a stable run identity from
the task and frozen execution configuration, and writes an `execution.json`
artifact atomically alongside the log, diff, and trajectory. The artifact
records execution only; verification, independent acceptance, and promotion
remain separate records. A missing provider, model, mini version, or Python
executable blocks the attempt instead of selecting a fallback.

## State separation

The following are distinct claims and must not be inferred from one another:

```text
HYPOTHESIS -> IMPLEMENTATION -> EXECUTED -> ACCEPTED -> PROMOTED
```

An experiment may stop at any state. `BLOCKED` and `NOT_EXECUTED` are not passes. A mechanism passing in isolation does not mean an executor has been adopted.

## Evidence discipline

- Record local evidence separately from upstream or scientific evidence.
- Preserve failures and blocked runs; do not replace them with a fallback result.
- Name every executor switch and every scope expansion before it happens.
- Keep generated artifacts outside version control unless they are small, intentional fixtures.

## Minimal template

Copy this template into a dated experiment record when the first executable capability is introduced:

```yaml
id: EXP-YYYY-MM-DD-name
hypothesis: "..."
scope: "..."
implementation: "..."
identity:
  codepro_revision: "..."
  dataset_revision_or_fingerprint: "..."
  task_ids: []
  base_revisions: []
  environment_image_digest: "..."
  verifier: "..."
attempts:
  experiment_id: "..."
  trial_id: "..."
  attempt_id: "..."
  verifier_run_id: "..."
executor: "..."
procedure: "..."
expected_signal: "..."
controls:
  negative_noop: {expected: "FAIL", evidence: []}
  positive_gold: {expected: "RESOLVED", evidence: []}
result: NOT_EXECUTED
evidence:
  local: []
  upstream: []
provider_called: UNKNOWN
acceptance: "PENDING"
promotion: NOT_PROMOTED
```
