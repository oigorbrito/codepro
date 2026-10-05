# Architecture boundary

The bootstrap architecture is intentionally small:

```text
CodePro
├── docs/          contracts, protocol, and decisions
├── experiments/   experiment records and fixtures; no implicit runtime
├── src/           small deterministic product and research contracts
├── tests/         executable verification boundary
└── tools/         dependency-free repository checks
```

P0 adds a deliberately small executable core under `src/arkx/`: versioned contracts, evidence status resolution, telemetry collection, and a deterministic baseline fixture. P1 adds explicit-signal task characterization, P2 adds snapshot-based progress assessment, P3 adds bounded routing/escalation policy, and Block B adds independent P4/P5/P6 artifacts in the same boundary.

Study Spec v1 adds a pre-execution research-design contract above P0-P6. It validates and content-addresses study design but does not execute a task, choose an executor, analyze results, accept evidence, or promote architecture.

The product surface includes a dependency-free `codepro` CLI implemented with the Python standard library. The CLI exposes help, version, doctor, and read-only project inspection. Inspection may query Git and PATH and detect project markers, but it does not invoke executors or execute tasks.

`codepro` is the canonical product and Python package namespace. The current
implementation remains under `src/arkx/` while `src/codepro/` provides the
staged public facade. Legacy `arkx` imports remain available during migration;
the facade does not imply that the wider API or installed-package behavior has
already been qualified. See Decision 0170 for migration criteria and status.

A low-level command environment boundary may execute an explicit argv vector with explicit cwd and timeout. Its output is a `CommandResult` observation only: exit code, stdout, stderr, timeout, duration, and environment error. It does not map process outcomes to task status.

Capability qualification is a separate pure boundary. A runtime executor identity is bindable only when the exact executor version + adapter version has explicit qualification evidence for the required capability. Availability alone is never qualification. Multiple equally qualified available executors are blocked rather than silently ranked.

Request/governance is an independent authority boundary. It can authorize scope, permissions, command/time budgets, an environment reference, and an acceptance authority. Missing information remains UNKNOWN; explicit denial is BLOCKED. Governance cannot choose an executor or declare acceptance.

No layer has a concrete Codex/Claude/Gemini adapter or executor orchestration.

## Boundary rules

- `src/` contains small, explicit, removable contracts and mechanisms only.
- `experiments/` contains evidence-oriented records and small fixtures, not an implicit runtime.
- `tools/` may validate repository contracts but must not become orchestration.
- `tests/` is the executable verification boundary.
- Integrations and executors require an explicit decision record and experiment evidence.
- A frozen study design is not an executed study; a content hash is not proof of temporal preregistration.

Creating a boundary or fixture does not imply that the corresponding capability is empirically validated.
