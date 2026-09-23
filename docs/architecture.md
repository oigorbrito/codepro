# Architecture boundary

The bootstrap architecture is intentionally small:

```text
Arkx
├── docs/          contracts, protocol, and decisions
├── experiments/   experiment records and fixtures; no runtime yet
├── src/           reserved product boundary; no implementation yet
├── tests/         reserved verification boundary; no test suite yet
└── tools/         dependency-free repository checks
```

P0 adds a deliberately small executable core under `src/arkx/`: versioned contracts, evidence status resolution, telemetry collection, and a deterministic baseline fixture. P1 adds explicit-signal task characterization, P2 adds snapshot-based progress assessment, and P3 adds bounded routing/escalation policy in the same boundary. No layer has a concrete executor interface or executor orchestration.

## Boundary rules

- `src/` is reserved for product code and is empty in this bootstrap.
- `experiments/` contains evidence-oriented records, not an implicit runtime.
- `tools/` may validate repository contracts but must not become orchestration.
- `tests/` contains P0 executable verification and remains the boundary for future tests.
- Integrations and executors require an explicit decision record and experiment evidence.

An empty boundary is intentional. Creating a directory does not imply that the corresponding capability exists.
