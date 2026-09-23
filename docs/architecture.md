# Architecture boundary

Arkx separates contracts, execution, verification, acceptance, and promotion.
The executable contracts cover the request-to-acceptance path. Runtime
capability is qualified per provider, model, executor, and treatment; the
presence of a contract does not imply adoption.

```text
Arkx
├── docs/          contracts, protocol, decisions, and evidence boundaries
├── experiments/   experiment records and synthetic fixtures; not orchestration
├── src/arkx/      executable contracts and bounded policy/runtime surfaces
├── tests/         executable contract and behavior verification
└── tools/         repository checks and narrow execution adapters
```

The current executable boundary is layered as follows:

- P0: versioned contracts, evidence status resolution, telemetry collection,
  and a deterministic baseline fixture;
- P1: explicit-signal task characterization;
- P2/P3: progress assessment, bounded routing, and evidence-based escalation;
- P4/P5/P6: repository planning/state, patch verification, and handoff/context
  accounting;
- P7/P8.1/P8.2: composition records, executor qualification contracts, and
  controlled treatment plans;
- P8.2a: a narrow Treatment A baseline runner and the official SWE-bench
  acceptance adapter;
- current orchestration surfaces: request governance, treatment/executor
  selection, sequential execution, recovery, independent acceptance, and
  promotion gates.

The canonical flow is:

```text
request
  -> governance / authority
  -> task characterization
  -> treatment route
  -> sufficient executor
  -> progress / recovery
  -> verification
  -> independent acceptance
  -> evidence for possible promotion
```

Routing selects the minimum sufficient treatment before selecting an executor.
Simple, localized, and repository-wide paths are capabilities/regimes, not
automatic executor cascades. A fallback, executor switch, scope expansion,
acceptance, or promotion must remain explicit and evidence-backed.

The official SWE-bench Docker authority has been qualified on the frozen Gold
tasks. That validates the acceptance path and infrastructure, not a real
provider/model, Treatment A execution, or A/B/C/D mechanism evidence.

## Boundary rules

- `src/arkx/` contains product contracts and bounded policy/runtime code; it
  must not silently grow into an unqualified general-purpose orchestrator.
- `experiments/` contains evidence-oriented records, not an implicit runtime.
- `tools/` may validate contracts or host a narrow adapter, but must not become
  an untracked orchestration layer.
- `tests/` verifies contracts and behavior; passing tests are local evidence,
  not scientific or upstream evidence.
- Integrations, providers, models, and executors require explicit identity,
  qualification evidence, and an acceptance authority.
- Missing provider/model identity, missing evidence, and blocked execution are
  preserved as blocked or unknown; they never become success.
- The working tree may contain an implementation under qualification. Merge
  readiness requires the corresponding decision record, tests, and evidence to
  be committed together.

The boundary is explicit: creating a module, fixture, or directory does not by
itself prove that the corresponding capability exists or is suitable for
promotion.
