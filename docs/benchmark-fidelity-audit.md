# Benchmark-fidelity architecture audit

## Purpose

This audit asks a stricter question than "does the CodePro code work?":

> When a CodePro mechanism is justified by benchmark or donor evidence, does the
> implementation preserve the execution assumptions that made that evidence valid?

A component that is original to CodePro is not required to look like an
upstream implementation. It is required to carry its own evidence and must not
inherit benchmark claims by association.

## Classification vocabulary

- `REFERENCE_MIRROR` — intentionally mirrors a pinned upstream artifact/mechanism.
- `REFERENCE_DERIVED` — adapts a documented upstream mechanism while preserving
  the relevant semantics.
- `CODEPRO_ORIGINAL` — local mechanism with local evidence only.
- `SYNTHETIC_ONLY` — implemented/tested with fixtures but not empirically qualified.
- `SUBSTRATE_MISMATCH` — copied scaffold/mechanism but changed an execution
  assumption material to the benchmark evidence.
- `AUDIT_REQUIRED` — insufficient evidence to classify.
- `PROMOTION_NOT_AUTHORIZED` — no evidence supports product tenure yet.

## Current findings

| Area | Current evidence | Classification | Audit conclusion |
|---|---|---|---|
| mini-SWE-agent SWE-bench execution substrate | Pinned mini v2.4.6 config selects Docker/Linux, /testbed, bash -c, BASH_ENV | `SUBSTRATE_MISMATCH` for Qualification Run v1 | Host-local Git Bash/MSYS2 must not be treated as benchmark-equivalent. Restore the pinned Docker substrate first. |
| P0 command observation | ADR 0024 explicitly adapts generic command-observation semantics from mini/SWE-agent/OpenHands; no benchmark-performance claim | `REFERENCE_DERIVED` as a generic contract | Valid as a CodePro observation boundary. It must not be reused as a substitute for the mini SWE-bench environment. |
| P1 task characterization | Synthetic fixtures only; ADR explicitly says accuracy is not established | `SYNTHETIC_ONLY` | Keep isolated from benchmark claims until tested on a frozen real workload. |
| P2 progress/stagnation | Synthetic fixtures; local adaptation of a generic idea | `SYNTHETIC_ONLY` | Thresholds and signals require empirical validation before affecting benchmark execution. |
| P3 routing/escalation | Synthetic fixtures; no executor authority | `SYNTHETIC_ONLY` | Must remain disabled in the benchmark baseline. Later treatment runs may test it as the manipulated variable. |
| P4 planning | Synthetic fixtures only | `SYNTHETIC_ONLY` | Do not inject into baseline mini runs before an explicit comparative study. |
| P5 patch verification contract | Synthetic fixtures only; separate from benchmark verifier | `CODEPRO_ORIGINAL` + `SYNTHETIC_ONLY` | It cannot replace the official SWE-bench verifier for benchmark claims. |
| P6 handoff accounting | Synthetic fixtures only | `CODEPRO_ORIGINAL` + `SYNTHETIC_ONLY` | Measurement-only instrumentation is acceptable if proven behavior-neutral. |
| Study-spec freeze | Local research-governance contract | `CODEPRO_ORIGINAL` | Appropriate as research infrastructure; no upstream performance claim is inherited. |
| Run provenance | Local research-governance contract | `CODEPRO_ORIGINAL` | Compatible with benchmark reproducibility goals. |
| Analysis-plan freeze | Local research-governance contract | `CODEPRO_ORIGINAL` | Does not alter agent execution and may remain around baseline runs. |
| Workload freeze | Local research-governance contract | `CODEPRO_ORIGINAL` | Must reference the exact benchmark dataset/subset/task list used by the upstream-equivalent run. |
| Validity plan | Local research-governance contract | `CODEPRO_ORIGINAL` | Does not confer validity by itself; evidence remains external. |
| Environment manifest | Local research-governance contract | `CODEPRO_ORIGINAL` | Must record container/image identity for benchmark runs; non-container justification cannot make a host-local run benchmark-equivalent. |
| Failure attribution | Local research-governance contract | `CODEPRO_ORIGINAL` | Useful and behavior-neutral if applied after raw evidence capture. |
| Treatment config freeze | Local research-governance contract | `CODEPRO_ORIGINAL` | Must include environment/backend identity, not only model/provider/prompt. |
| Measurement contract | Local research-governance contract | `CODEPRO_ORIGINAL` | Official verifier outcome must remain the source for SWE-bench resolution claims. |
| Protocol deviations | Local research-governance contract | `CODEPRO_ORIGINAL` | Backend/substrate changes must be recorded as configuration/executor deviations rather than silently normalized. |
| Promotion gate | Local research-governance contract | `CODEPRO_ORIGINAL` | Correctly prevents a local mechanism pass from becoming product tenure. |
| Executor qualification/binding | Original CodePro contract informed by explicit identities in benchmark harnesses | `REFERENCE_DERIVED` | Suitable if exact adapter + environment/backend identity is part of qualification evidence. |
| Governance | Original CodePro authority boundary | `CODEPRO_ORIGINAL` | Keep separate from benchmark runtime; it must not rewrite benchmark configuration. |
| Recovery controller | Local mechanism with focused tests | `CODEPRO_ORIGINAL` | Must be disabled in the first reference baseline unless the upstream run has equivalent retry/recovery semantics. |
| Independent acceptance | Local post-verification decision | `CODEPRO_ORIGINAL` | May consume benchmark evidence; must not alter the benchmark execution itself. |
| Promotion binding | Local post-acceptance decision | `CODEPRO_ORIGINAL` | Behavior-neutral with respect to the benchmark run. |

## Baseline rule

The first corrected qualification line must be a reference baseline, not a
CodePro treatment.

For that baseline:

- use mini-SWE-agent v2.4.6 at the pinned commit;
- use its bundled SWE-bench configuration unchanged;
- use Docker/Linux task environments;
- use the benchmark task image derived by the pinned runner;
- retain the upstream prompt/tool/step/cost/environment semantics;
- disable CodePro routing, recovery, compaction, fallback, handoff, replanning
  and other behavior-changing mechanisms;
- collect CodePro observability only where it is demonstrated not to alter the
  treatment;
- evaluate the produced patch using the official/frozen SWE-bench verifier.

## Required follow-up audit

For every behavior-changing CodePro capability proposed after the baseline,
record:

1. the upstream benchmark/paper/donor result that motivated it;
2. exact version/commit and experiment conditions;
3. which mechanism is copied;
4. which assumptions are preserved;
5. which assumptions differ;
6. whether the difference is an intended treatment variable or an accidental
   implementation deviation;
7. a reference-baseline vs treatment experiment on the same frozen workload;
8. quality, cost, token, wall-time, reliability and verifier metrics;
9. protocol-deviation handling;
10. promotion decision based on measured evidence.

No component receives tenure merely because it already exists in the repository.

## Immediate audit priorities

1. Restore and execute the pinned mini Docker baseline.
2. Verify official SWE-bench patch/verifier flow end to end.
3. Audit provider/model adapter semantics against the exact runs used as external
   comparators.
4. Audit timeout, retry and recovery semantics.
5. Audit routing/escalation treatment against benchmark baselines.
6. Audit compaction/context changes against token/cost/quality evidence.
7. Audit handoff/multi-executor behavior against a fixed same-task comparator.
8. Audit instrumentation overhead and prove observation does not alter behavior.

## Qualification lineage

Qualification Run v1 remains:

- `Gate A = PASS`
- `Gate B = BLOCKED`
- `verifier = NOT_EXECUTED`
- `promotion = NOT_AUTHORIZED`
- `Qualification Run v1 = BLOCKED`

The benchmark-faithful Docker substrate starts a new qualification lineage. It
does not retroactively repair or reinterpret v1.
