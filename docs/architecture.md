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

The product surface now includes a minimal `codepro` CLI implemented with the Python standard library. The CLI exposes help, version, and a read-only doctor command only; it does not invoke executors or execute tasks.

No layer has a concrete executor interface or executor orchestration.

## Boundary rules

- `src/` contains small, explicit, removable contracts and mechanisms only.
- `experiments/` contains evidence-oriented records and small fixtures, not an implicit runtime.
- `tools/` may validate repository contracts but must not become orchestration.
- `tests/` is the executable verification boundary.
- Integrations and executors require an explicit decision record and experiment evidence.
- A frozen study design is not an executed study; a content hash is not proof of temporal preregistration.

Creating a boundary or fixture does not imply that the corresponding capability is empirically validated.
