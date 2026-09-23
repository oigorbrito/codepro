# Arkx — architectural audit, 2026-09-23

## Scope and evidence boundary

This is a read-oriented architectural audit of the current working tree on
branch `codex/auditoriaarquitetural`, at HEAD `d54262aa`. The checkout contains
the committed architecture, documentation, tests and evidence plus two nested
experimental workspaces with local modifications. Those workspaces were
inspected and preserved; unrelated changes were not reset or deleted.

Evidence inspected included the P0–P8 history, decision records 0012–0083,
contracts, tests, runners, adapters, telemetry, experimental manifests,
evaluation logs, and the current package API. The complete deterministic local
suite passed: 367 tests. This is local evidence only. It is not provider,
model, Docker, SWE-bench, benchmark, or scientific qualification evidence.

The current external authority boundary remains explicit: the official
SWE-bench Docker Gold path is recorded as `resolved: true` for frozen tasks,
but the real provider/model and the A/B/C/D mechanism trial remain
unqualified. Local OpenRouter/minisweagent and Git Bash paths are blocked;
Docker access is blocked by infrastructure permissions; Ollama identity and
configuration are not frozen sufficiently for qualification.

## Module audit

The entries below use the requested dimensions in compact form:
responsibility/API/invariants; dependencies and coupling; error/recovery;
idempotency and persistence; observability/tests; risks/debt/maturity.

| Module | Responsibility, contract and invariants | Dependencies, errors, recovery, persistence and tests | Coupling, risks and maturity |
|---|---|---|---|
| request | Authorizes a request with task, scope, authority, environment and budget. Public request/governance contracts reject missing authority/scope/budget and preserve explicit blocked state. | Upstream of characterization/routing/selection. Error is blocked governance; no executor recovery. Deterministic serialization and request tests exist. | Provider/model-independent, but policy semantics are still embedded in request types. `FUNCTIONAL_BUT_WEAK`. |
| selection | Selects a treatment and executor binding from explicit registries and qualification status. | Depends on routing/treatment definitions and executor registry; blocks rather than cascades. Selection tests cover advertised capabilities and invalid bindings. | Executor identity/capability fields still enter selection; no full capability discovery or dynamic registry persistence. `FUNCTIONAL_BUT_WEAK`. |
| localization | P8.2 evidence-budgeted candidate file/symbol/context localization. | Depends on repository input and explicit evidence budget; overflow is deterministic and non-retryable. Artifacts serialize evidence budget; focused tests exist. | Treatment-specific P8.2 implementation, not yet a generalized localization protocol. `PARTIAL`. |
| editing | P8.2 edit artifact contract and patch validation. | Depends on localization and repository paths; invalid/missing patch evidence blocks. Persistence is artifact-based; tests cover deterministic patch boundaries. | Still treatment/P8.2 shaped and not a universal edit operation protocol. `PARTIAL`. |
| orchestration | Sequentially composes governance, characterization, routing, selection, preflight, execution, progress, verification, acceptance and terminal telemetry. | Depends on all gates and optional event log. It separates verification/acceptance and never selects fallback executors. Budgeted plans require `run_with_budget`; persistence failures are explicit. Tests cover order, gates, terminal event and capability preflight. | Central seam is still a large composition function and replay-driven resume remains outside the live pipeline. `FUNCTIONAL_BUT_WEAK`. |
| acceptance | Independent authority converts verification into explicit acceptance result. | Depends on verification evidence and authority identity; mismatch/blocked/indeterminate states are preserved. Causal verification reference is included. Tests cover decisions and boundary failures. | Authority contract is explicit, but policy composition and durable authority evidence remain thin. `FUNCTIONAL_BUT_WEAK`. |
| verification | Neutral verification result separates pass/fail/blocked/indeterminate/not-executed from execution. | Depends on execution artifacts/evaluator boundary; failures map to explicit outcome/error envelopes. Tests cover outcome mapping and causal reference. | Verifier protocol exists; evaluator abstraction and multiple concrete verifiers are not generalized. `FUNCTIONAL_BUT_WEAK`. |
| recovery | Bounded recovery/replan budget and lineage contracts. | Depends on prior attempt identity and explicit retry/recovery policy; no implicit executor switch. Lineage persists in artifact store and is replay-auditable. Tests cover exhausted budget and identity drift. | Planner is not yet integrated into the main orchestration lifecycle as a first-class state transition. `PARTIAL`. |
| promotion | Gate that requires independent acceptance plus matching verification and causal references. | Depends on verification/acceptance and manifest state; rejects mismatch and lacks automatic promotion. Promotion event requires prior acceptance in event log. Tests cover rejection and event persistence. | Good boundary, but promotion is not yet a fully independent persisted workflow with operator decision records. `FUNCTIONAL_BUT_WEAK`. |
| baseline / execution | Neutral `Executor`, `ExecutionRequest`, `ExecutionPlan`, `ExecutionResult`, budgets, retry policy, capability profiles and fake implementations. | Downstream adapters execute; upstream orchestration plans. Contract lifecycle and budget ledger are immutable/idempotent. Budget enforcement is an explicit runner capability with deterministic rejection when absent. | External concrete execution remains blocked/unqualified and legacy callers without the capability remain blocked. `FUNCTIONAL_BUT_WEAK`. |
| provider adapters | Provider protocol and normalized provider error envelope exist. | Provider failures preserve raw context and retryability; concrete OpenRouter path is import-safe but execution-strict. Adapter preflight records identity/dependencies. | Provider identity, model and configuration still live in P8.2 adapter surfaces; no independently qualified provider registry. `EXPERIMENT_COUPLED`. |
| executor adapters | Executor protocol, preflight, capability profile, and P8.2 baseline adapter exist. | Adapter errors map to neutral domains; minisweagent absence and Git Bash access failure remain explicit blocked/unknown. | Concrete adapter is still a qualification/treatment adapter rather than a stable production plugin boundary. `EXPERIMENT_COUPLED`. |
| telemetry | Event contracts, lifecycle counters, replay state, structured error codes and terminal facts. | Depends on event log and artifact references; deterministic reduction exists; malformed/missing facts remain incomplete/ inconsistent. Tests cover replay, telemetry consistency and terminal immutability. | No shared trace correlation across all external process/provider logs; telemetry is mostly event-level. `FUNCTIONAL_BUT_WEAK`. |
| error taxonomy | Neutral `ErrorDomain`, `ErrorEnvelope`, retryability and adapter normalization. | Upstream adapters and downstream retry/recovery consume it; unknown/blocked are preserved. Tests cover provider/process/exception/preflight mappings. | Codes are still partly stringly typed and executor-specific codes can leak in `raw` fields. `FUNCTIONAL_BUT_WEAK`. |
| task state | `RunState`, transition validation, orchestration status and explicit terminal lifecycle. | State transitions are deterministic and terminal states immutable. Manifest and event log both persist state-related facts. Tests cover illegal transitions and replay mismatch. | Two state vocabularies (`RunState` and `OrchestrationStatus`) are bridged manually; no single lifecycle state machine authority. `FUNCTIONAL_BUT_WEAK`. |
| artifact/state persistence | Atomic manifest/artifact store, attempt/retry lineage, event log, audit and replay. | Depends on stable references and identity digests; incomplete chains are not accepted. Tests cover atomicity, audit, comparison and replay. | Cross-file persistence is deliberately audit-based, not transactionally atomic; real-runtime crash-resume effectiveness remains unqualified. `FUNCTIONAL_BUT_WEAK`. |
| experimental protocol | Frozen task/treatment identity, manifests, comparability and qualification gates. | Depends on provider/model/config/budget/runtime identity and raw logs. Blocks missing identity and separates local evidence from external authority. Tests cover audited experiments and comparability. | Experimental protocol is strong conceptually but still P8.2-shaped and lacks a universal experiment service. `FUNCTIONAL_BUT_WEAK`. |
| configuration | Configuration digests and typed secret-safe snapshots exist on plans, adapters and experiments. | Configuration is passed through request/plan/adapter identities; orchestration retains a supplied snapshot and rejects digest mismatch. | Propagation remains optional for legacy callers and there is no universal resolution record for every adapter. `FUNCTIONAL_BUT_WEAK`. |
| CLI / entrypoints | Tools and scripts expose baseline/preflight/probe flows. | Entrypoints preserve strict failure and write logs/manifests where implemented. Tests cover selected tools, not every invocation path. | CLI surface is experimental and not a stable public command contract. `PARTIAL`. |
| package/public API | `arkx.__init__` exports neutral contracts, lifecycle, routing, integration and audit APIs. | Import boundaries are tested and optional dependencies are lazy/strict at execution. | Public API is broad and currently exposes both legacy P8.2 and neutral seams without deprecation/version policy. `FUNCTIONAL_BUT_WEAK`. |

## 1. Architecture Gap Matrix

| módulo | maturidade | principal fraqueza | impacto | dependências | ação necessária |
|---|---|---|---|---|---|
| request | FUNCTIONAL_BUT_WEAK | policies embedded in request | inconsistent policy evolution | governance, routing | extract versioned policy inputs |
| selection | FUNCTIONAL_BUT_WEAK | shallow capability/qualification input | wrong treatment binding | registry, routing | capability-aware selection contract |
| localization/editing | PARTIAL | P8.2-specific contracts | poor composition | treatment, repository | generalize evidence and edit interfaces |
| orchestration | FUNCTIONAL_BUT_WEAK | monolithic composition seam | hard isolated evolution; live resume remains external | all gates | split plan/run/gate/persist services when empirical consumers require it |
| acceptance/verification | FUNCTIONAL_BUT_WEAK | evaluator/authority implementations thin | false confidence or blocked decisions | artifacts, authority | evaluator/verifier adapters and independent records |
| recovery | PARTIAL | not a first-class lifecycle stage | incomplete resume/replan | attempt store, retry | integrate recovery planner and state transitions |
| promotion | FUNCTIONAL_BUT_WEAK | event exists but workflow is thin | premature or non-reproducible promotion | acceptance, verification | durable promotion gate record |
| execution/baseline | FUNCTIONAL_BUT_WEAK | external adapters remain unqualified | portability and operational uncertainty | executor runners | qualify concrete combinations; keep non-capable legacy runners blocked |
| provider/executor adapters | EXPERIMENT_COUPLED | concrete paths tied to P8.2/runtime | portability and qualification risk | minisweagent, OpenRouter, Git Bash | stable plugin adapters plus capability qualification |
| telemetry/errors | FUNCTIONAL_BUT_WEAK | string codes and partial trace correlation | diagnosis/replay friction | event log, artifacts | canonical error/trace schema |
| task state/persistence | FUNCTIONAL_BUT_WEAK | dual vocabularies and audit-based cross-file persistence | divergent replay/resume under real crashes | manifests, event log | retain explicit crosswalk; add stronger coordination only for concurrent/distributed consumers |
| protocol/config/CLI/API | PARTIAL / FUNCTIONAL_BUT_WEAK | no central versioned config/CLI policy | reproducibility and compatibility debt | all modules | versioned schemas and compatibility policy |

## 2. Missing Architecture

Remaining or conditionally required architecture, not all immediately required:

1. A concrete adapter qualification registry that persists capability
   provenance and qualification authority independently from selection.
2. A coordinated resume/replay protocol that defines what may be resumed after
   a crash and what must remain blocked or indeterminate.
3. A stable evaluator/verifier adapter boundary with raw result retention and
   multiple independently exercised concrete verifiers.
4. A single lifecycle state machine is optional at current scope: the explicit
   `RunState`/`OrchestrationStatus` crosswalk is the current tested decision.

Already present and therefore not recommended for speculative duplication:
neutral Executor/Provider/Sandbox protocols, capability registry, routing
decision, execution plan, artifact store, event log/replay, budget ledger,
retry policy, recovery lineage, promotion gate, and experiment identity digest.
An event bus would be overengineering now; the append-only event log is enough
until multiple independent consumers or distributed execution require fan-out.

## 3. Coupling Map

```text
request -> routing -> selection -> orchestration -> ExecutorRunner
                                      |                |
                                      |                +--> P8.2 baseline/minisweagent
                                      |                +--> provider/model config
                                      |                +--> Docker/Git Bash/Ollama runtime
                                      |
                                      +--> verification/evaluator
                                      +--> acceptance authority
                                      +--> event log/artifact store

P8.2 treatment ----> localization/editing ----> SWE-bench authority
provider/model ----> preflight + execution logs
Docker ------------> baseline qualification and external authority
SWE-bench ---------> authority result, not neutral execution contract
```

The leaks are concentrated in concrete adapter and qualification layers, while
the orchestration seam now blocks a runner without an explicit budget-
enforcement capability. SWE-bench is correctly outside the neutral execution contract;
the remaining risk is that P8.2 assumptions enter through selection and runner
interfaces rather than through an explicit treatment adapter.

## 4. Critical Path

1. Qualify at least one real executor/provider/sandbox combination with the
   already-established identity, preflight, budget, and replay gates.
2. Split orchestration into plan, preflight, execute, verify, accept and
   persist components with one lifecycle state authority.
3. Generalize evaluator/verifier and recovery seams, including crash-resume
   rules.
4. Freeze a versioned configuration snapshot and trace identity across all
   adapter logs.
5. Do not use a provider result to infer architecture quality; acceptance and
   promotion remain independent authorities.

## 5. Parallelizable Work

Can proceed without waiting for any external executor result:

- lifecycle state-machine consolidation;
- evaluator/verifier adapter contract;
- recovery planner integration tests using fake executor/provider/sandbox;
- configuration snapshot schema and canonical digest tests;
- crash/replay/resume property tests;
- adapter capability registry and qualification-record tests;
- CLI contract tests and package API deprecation/version checks;
- update of the experimental protocol to require these identities.

## 6. Experiment-dependent

Must wait for infrastructure or external evidence:

- qualification of OpenRouter/minisweagent execution;
- Docker/SWE-bench authority runs;
- provider/model mechanism comparison;
- real sandbox performance, timeout and cost distributions;
- empirical retry/recovery effectiveness;
- promotion of any executor, model, provider or treatment.

## Latest local verification

The lineage-event-chain audit block was verified with the focused replay and
restored-chain tests, followed by the complete deterministic suite: 365 tests
passed. This is local evidence only; it does not qualify a real provider,
model, executor, sandbox, or SWE-bench treatment.

The budget-enforced legacy-runner block was then verified with the complete
deterministic suite: 366 tests passed. A budgeted plan now blocks a runner that
cannot declare `run_with_budget`; the neutral contract bridge is the first
implementation of that boundary. This closes the previously identified silent
legacy budget-bypass gap locally, but does not qualify any external runner.

The orchestration-configuration-snapshot block was then verified with 367
passing deterministic tests. A supplied typed snapshot now survives into the
execution plan and is checked against executor identity; legacy callers without
one remain explicitly weaker rather than being upgraded by inference.

## Conclusion

Arkx is no longer merely a collection of executor-specific experiments: the
neutral contract, capability, lifecycle, audit and replay foundations are
materially present. It is not yet a complete executor-agnostic architecture.
The decisive remaining issues are concrete adapter qualification and empirical
validation of retry/recovery under real runtimes. Persistence coordination is
deliberately audit-based at the current single-process scope; a transaction
coordinator or event bus is deferred until concurrent or distributed consumers
create evidence for that need. Budget enforcement and typed configuration
identity now have explicit local gates, while legacy callers without the new
evidence remain blocked or weaker rather than being upgraded by inference.
