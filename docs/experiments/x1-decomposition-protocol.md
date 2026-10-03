# CodePro X1 — Frozen Protocol

**Protocol ID:** `X1-TOPOLOGY-001`  
**Status:** `FROZEN_SPECIFICATION / CELLS_NOT_AUTHORIZED`  
**Scope:** compare monolithic execution, static decomposition, and runtime DAG decomposition with node-local retry.  
**Authority:** research protocol derived from issue #93; does not authorize model/scaffold execution, Phase 7Q cells, Phase 8, or promotion.

## 1. Decision boundary

This document freezes the comparison contract. It is not evidence that any X1 treatment ran.

```text
EXTERNAL_BENCHMARK_SIGNAL != CODEPRO_LOCAL_PROOF
PROTOCOL_FROZEN != CELL_AUTHORIZED
CELL_EXECUTED != VERIFIED
VERIFIED != ACCEPTED
ACCEPTED != PROMOTED
```

The current records report `Phase 7R = COMPLETE / NO_COMPATIBLE_SURVIVOR`, `Phase 8 = BLOCKED_BY_NO_COMPATIBLE_SCAFFOLD`, and Phase 7Q pair recovery still in progress. The recorded S4-L1-Q1 attempts did not reach model/scaffold execution because of Windows Application Control blocking the frozen runtime. Therefore **A, B, and C are all currently `NOT_AUTHORIZED`**. Do not run a real-model, scaffold, or task-solving X1 cell until a compatible path is explicitly accepted through the governing Phase 7Q/8 decisions.

Allowed before that gate: schema validation, synthetic fixture generation, dry-run planning, offline metric/validator tests, and replay of already preserved trajectories. Label all such outputs `NON_EXPERIMENTAL`; none may be described as X1 results.

## 2. Frozen estimand and hypothesis

**Unit:** one frozen task/repository revision, run under all three treatments as a matched block.

**Primary hypothesis:** runtime DAG decomposition (C) reduces tokens spent after the first failed node relative to monolithic execution (A), without materially reducing independently verified task resolution.

**Primary comparisons:** C vs A for retry-token ratio and verified resolution. B vs A and C vs B are secondary; no candidate is assumed superior.

```text
retry_token_ratio = input_tokens_after_first_failed_node
                    + output_tokens_after_first_failed_node
                    ------------------------------------------------
                    initial_attempt_input_tokens
                    + initial_attempt_output_tokens
```

If no node fails, numerator is zero and `first_failed_node = null`; preserve this case and report it separately. A failed initial attempt with unknown token accounting has a missing primary metric, not an imputed value.

## 3. Treatments

All treatments receive the same task statement, initial repository state, model/scaffold/runtime identities, tool permissions, verifier, wall-clock ceiling, token ceiling, and total call ceiling. Only decomposition/recovery policy differs.

| ID | Treatment | Frozen behavior |
|---|---|---|
| A | `MONOLITHIC` | One agent trajectory owns the task. It may make ordinary within-trajectory tool calls and retries under the common ceilings. No task partition or dependency DAG is supplied. |
| B | `STATIC_DECOMPOSITION` | Before execution, a fixed decomposition manifest divides the task into ordered subtask nodes and dependencies. The manifest is immutable during the run. A failed node may be retried only if the exact frozen baseline policy already permits it; no runtime repartition/replan. |
| C | `RUNTIME_DAG_LOCAL_RETRY` | Start from the same task. A planner may create a DAG using the frozen node schema. Validate schema and graph before dispatch. Execute only dependency-ready nodes. A node failure may retry that node and its declared downstream dependents only; preserve successful unaffected nodes and their outputs. Any graph rewrite is a replan and must be logged. |

No multi-agent parallelism is introduced by this protocol. Execute ready nodes serially (`concurrency=1`) in B and C to isolate topology and retry locality from parallelism. C must not silently fall back to A or B. Schema rejection, cycle, missing dependency, invalid output, or exhausted budget is a treatment failure, not a reason to repair the graph outside the run.

## 4. Hard preconditions (fail closed)

Before any cell starts, create a signed/hashed run manifest and assert all gates below. If any gate is false or unknown, report `BLOCKED_PREFLIGHT` and do not invoke a model or scaffold.

1. A governing decision explicitly authorizes the exact compatible model/scaffold pair and X1 cells after Phase 7Q/8 review. Phase 7Q artifact identity alone is insufficient.
2. Model, quantization/artifact hash, scaffold version/commit, runtime/server, provider, OS, tool schema, prompt profile, context, sampling, and relevant environment are pinned and recorded.
3. Independent verifier and E2E/integration acceptance path are available and versioned. X6 baseline gate is recorded as passed for the exact execution path, or the governing decision explicitly documents an equivalent accepted gate.
4. Task/repository fixtures, train/pilot/held-out split, budget, repetition order, and thresholds below are frozen before any treatment result is inspected.
5. A/B/C can all be run on the same hardware and execution route without fallback or material environment drift.
6. Instrumentation captures per-call token usage from authoritative runtime/provider counters. If unavailable, token measures are `UNKNOWN`; do not substitute estimates in primary analysis.
7. Scratch worktrees and evidence destinations are isolated and cleanup is observable. No treatment may alter the source fixture or another treatment's worktree.

Record each check as `{gate_id, status: PASS|FAIL|UNKNOWN, evidence_ref}`. Only all-PASS opens the cell authorization request; this protocol itself does not issue that authorization.

## 5. Fixture and dataset contract

Do not invent or retrofit task outcomes. Select fixtures from a named, licensed/authorized task corpus and preserve exact source revision and task text. Freeze at least **20 tasks** before opening results: at least 10 single-file and 10 multi-file; include dependency-free and dependency-bearing tasks, and at least two repository-size bands that fit the qualified hardware. If this composition cannot be met, mark the dataset `INCOMPLETE` and defer the comparison.

Reserve a held-out set of at least 25% (minimum 5 tasks), stratified by file-count/dependency class and repository-size band, before pilot/tuning. Held-out tasks cannot be used to alter prompts, decomposition schema, thresholds, budgets, or implementation. If a fixture corpus provides fewer than 20 eligible tasks, report a protocol deviation and do not make a general KEEP decision.

Each immutable fixture record must contain:

```json
{
  "task_id": "stable-id",
  "corpus": "name-and-version",
  "repo_url": "canonical-source",
  "repo_revision": "full-commit-sha",
  "task_text_sha256": "hex",
  "language": "value",
  "repo_size_bytes": 0,
  "tracked_file_count": 0,
  "expected_changed_paths": ["relative/path"],
  "dependency_edges": [["node-a", "node-b"]],
  "verifier_id": "name@version-or-commit",
  "e2e_verifier_id": "name@version-or-commit",
  "budget_profile_id": "frozen-profile",
  "split": "pilot|heldout"
}
```

`dependency_edges` describe task-level required ordering/dependencies, not the C planner's observed DAG. Preserve both separately. The same fixture bytes/revision must seed each matched run. Reject dirty or non-identical seeds.

## 6. Controlled variables and run order

Freeze a machine-readable `x1-manifest.json` with all identities and values before execution. At minimum record:

```text
protocol_id, protocol_sha256, dataset_manifest_sha256, codepro_commit
model_name, model_artifact_sha256, quantization, context_limit, sampling_config
scaffold_name, scaffold_version, scaffold_commit, runtime/server identity
provider, OS/build, hardware identifiers, tool schema/prompt hashes
verifier and E2E verifier identities
per-run max input/output/total tokens, max calls, max wall seconds
concurrency=1, retry policy, retry cap, planner/schema versions
seed policy, repetition count, treatment order, timestamps
```

Use **5 repetitions per task per treatment**. Match by `(task_id, repetition_index)`. For each matched block, rotate treatment order with a fixed, published seed; preserve the generated order file. Use a fresh isolated worktree for each treatment-run. No adaptive budget increase, prompt repair, model swap, tool change, or manual intervention is permitted mid-run. A necessary change invalidates the run and requires a new protocol revision and authorization.

The common per-run token/call/wall ceilings must be populated in the manifest from the qualified path's already approved budget. This protocol does not guess hardware feasibility or authorize budget changes. Missing budget values block execution.

## 7. Runtime DAG contract for C

The C planner output must validate against this logical schema before any node executes:

```json
{
  "nodes": [
    {"id":"n1", "goal":"...", "depends_on":[], "input_refs":[], "output_schema":"..."}
  ],
  "terminal_nodes": ["n1"]
}
```

Reject duplicate IDs, unknown dependencies, cycles, unreachable nodes, empty goals, undeclared inputs, missing output schemas, or terminal nodes not in the graph. Persist exact planner input/output and validation errors.

Each node result must record status, input/output artifact hashes, declared output-schema validation, start/end times, tool-call IDs, token counters, attempt number, and error classification. On retry, replay only the failed node plus descendants whose declared inputs became invalid. Do not rerun successful independent nodes. If dependency invalidation cannot be determined from declared edges and input hashes, fail closed and classify `INVALIDATION_AMBIGUOUS`.

## 8. Raw observations (retain per call and per run)

Never replace raw observations with a composite score. Required per-call fields:

```text
run_id, task_id, repetition_index, treatment, call_id, node_id|null
attempt_number, retry_of_call_id|null, replan_id|null
start_utc, end_utc, status, failure_class, tool_names
input_tokens, output_tokens, cached_input_tokens|null, source_of_counter
input_artifact_hashes, output_artifact_hashes, prompt_hash
```

Required per-run fields:

```text
preflight_gate_results, task_resolution_status
independent_verifier_status + raw output/hash
integration_e2e_status + raw output/hash
total input/output tokens and unknown-counter flags
total calls, retries, replans, failed-node reruns
wall time (including planning, retries, verification; also component times)
duplicated_work_units and calculation trace
changed paths, diff hash, source cleanliness, worktree cleanup status
budget exhaustion, interruption, infra/harness failure classification
```

`duplicated_work_units` is the sum of repeated execution units keyed by `(task_id, node_id, normalized action/input hash)`, counted only when an equivalent unit is executed again. Preserve the event list and normalization version. Also report rerun nodes and rerun output bytes as direct measures; do not infer duplication from tokens alone.

Keep all failed, timed-out, invalid, and interrupted runs in the denominator and raw archive. Harness/infra failures are labeled separately; they are not silently dropped or recoded as model failures. A rerun after an infrastructure failure gets a new run ID and links to the original.

## 9. Derived metrics and analysis

Per treatment, report raw numerator/denominator and missingness alongside:

* verified resolution: count `E2E_PASS` / all assigned runs, plus independent-verifier pass and E2E pass separately;
* total input tokens, output tokens, calls, retries, replans, failed-node reruns;
* retry-token ratio as defined in §2;
* wall-clock total and stage times;
* duplicated-work units, rerun nodes, rerun output bytes;
* invalid DAG/schema rate for C; integration failures and harness/infra failures;
* total cost only if a frozen, auditable price/compute accounting source exists; otherwise `NOT_MEASURED`.

Show task-level paired results and distributions, not only averages. For the two primary comparisons, compute a paired, task-clustered bootstrap 95% confidence interval with 10,000 resamples and fixed seed `X1-2026-01`; publish script/version and resampled statistic. Do not treat five repetitions of one task as five independent tasks. Report per-repetition observations and task-level aggregates.

**Predeclared practical thresholds:**

* C must reduce the task-level median retry-token ratio by at least 10% vs A, and the paired 95% interval for the reduction must exclude zero.
* C's E2E verified-resolution difference vs A must have a 95% interval lower bound no worse than `-5 percentage points`.
* C must not increase median total tokens by more than 5% vs A unless E2E verified resolution improves by at least 5 percentage points and the confidence interval excludes zero.
* Any hard authority, scope, data-integrity, or verifier failure blocks acceptance regardless of aggregate metrics.

Apply the same criteria to held-out after the mechanism and analysis code are frozen on pilot. If the held-out set is too small for an informative interval, classify `INCONCLUSIVE`, not PASS. B is analyzed identically as a comparator; these thresholds do not authorize B or C.

## 10. Required evidence bundle

One immutable evidence directory per protocol batch; one subdirectory per run. Include:

```text
x1-manifest.json                 # frozen identities, budgets, seeds, gates
dataset-manifest.json            # fixture hashes and split
run-order.csv                    # matched blocks and randomized order
raw/calls.jsonl                  # per-call telemetry
raw/events.jsonl                 # node/retry/replan/dependency events
raw/verifier/                     # full verifier and E2E outputs
raw/diffs/                        # exact patch/diff or explicit no-patch record
derived/metrics.csv              # one row per run, no hidden exclusions
derived/analysis.json            # methods, intervals, seeds, missingness
derived/decision.json            # KEEP|REMOVE|DEFER and rule references
logs/                             # runner stdout/stderr and environment capture
SHA256SUMS                        # hashes for every evidence file
```

Every missing artifact must be represented by a reason-coded record. Preserve secrets out of evidence; use redacted values with a stable reference/hash and document the redaction. Do not overwrite a prior evidence directory. Archive the exact code commit and analysis script hash.

## 11. Decision rules

Decide each mechanism separately; external papers do not count toward local thresholds.

* **KEEP (candidate for later acceptance review):** all hard gates pass; all five repetitions and held-out evidence are complete; C meets both primary thresholds on held-out; the total-token rule is met; results reproduce from frozen artifacts; and added planner/schema/retry complexity is fully represented in operational metrics. KEEP does not promote or select the mechanism.
* **REMOVE:** valid, sufficiently powered evidence shows the primary gain is absent or below threshold, a material held-out regression occurs, total operational cost is unjustified, or the mechanism violates an authority/correctness invariant. Preserve the negative result.
* **DEFER:** any prerequisite is blocked/unknown; fewer than 20 eligible frozen tasks or incomplete held-out; instrumentation cannot capture required raw counters; confidence intervals are inconclusive; environment drift invalidates comparability; or a harness/infra failure prevents valid interpretation.

Until execution is separately authorized, the protocol's present disposition is:

```text
X1_PROTOCOL = FROZEN_SPECIFICATION
X1_A/B/C = NOT_AUTHORIZED
X1_RESULT = NOT_RUN
X1_DECISION = DEFER (BLOCKED_PHASE7Q_8_COMPATIBLE_PATH)
PROMOTION = NOT_AUTHORIZED
```

## 12. Execution entrypoint contract (future; not a command to run now)

An implementation must expose a dry-run/preflight command that cannot invoke a model:

```text
codepro-x1 preflight --manifest x1-manifest.json --dataset dataset-manifest.json
```

It must exit nonzero unless every §4 gate is PASS, all manifest hashes resolve, and all three treatments are available under the exact frozen identities. Only a separate authorization record may enable execution:

```text
codepro-x1 run --authorization x1-cell-authorization.json \
  --manifest x1-manifest.json --dataset dataset-manifest.json \
  --evidence-root <new-empty-directory>
```

The runner must refuse execution if the authorization record does not identify this protocol hash, exact cells, model/scaffold pair, dataset hash, budget profile, and approving Phase decision. A dry-run must clearly print `MODEL_INVOCATIONS=0`. This document supplies no authorization record and does not define a live command path in the current repository state.

## Sources checked

* Issue [#93](https://github.com/oigorbrito/codepro/issues/93), created 2026-10-03: research plan and explicit non-promotion/precondition rules.
* PR [#92](https://github.com/oigorbrito/codepro/pull/92), head `95248a5d4f9e589a7ab80fd778e28cb5d15ab57f`: Phase 7Q artifact identity recovery; Phase 8 remains blocked absent a compatible path; S4-L1-Q1 did not reach model/scaffold execution due to Windows Application Control.
* `roadmap.md` at default branch head `83ea3868994b549605341c0a535e9f1a70611734`: Phase 7 complete, zero compatible survivors, Phase 8 blocked.

