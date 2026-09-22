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

## Boundary rules

- `src/` is reserved for product code and is empty in this bootstrap.
- `experiments/` contains evidence-oriented records, not an implicit runtime.
- `tools/` may validate repository contracts but must not become orchestration.
- `tests/` is reserved for executable verification as capabilities are added.
- Integrations and executors require an explicit decision record and experiment evidence.

An empty boundary is intentional. Creating a directory does not imply that the corresponding capability exists.

