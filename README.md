# CodePro

**Executor-agnostic software-engineering chassis developed through explicit contracts, falsifiable hypotheses, and reproducible evidence.**

> **MINIMUM SUFFICIENT ARCHITECTURE**  
> **FOR MAXIMUM RELIABLE CAPABILITY**

CodePro is not designed around “adding more agents”. Its core question is narrower:

> **Which mechanisms measurably improve verified software-engineering capability enough to justify their token, latency, operational, and architectural cost?**

The repository is the canonical project root.

---

## Current state

Repository reconciliation is complete.

```text
R1 = DONE
R2 = DONE
R3 = DONE
R4 = DONE
R5 = DONE

RECONCILIATION = DONE
NORMAL ROADMAP = RESUMED
CURRENT PHASE = PHASE 7 / SCAFFOLD COMPATIBILITY
```

The reconciled main preserves:

- the Python `arkx` operational core;
- the public `codepro` CLI;
- the Python regression and validation boundary;
- the TypeScript/API/UI surface;
- a real TypeScript -> Python vertical execution adapter;
- executor/provider qualification tooling;
- post-deviation telemetry and local-runtime evidence.

Final R5 requalification included:

```text
package install                    PASS
CLI version / doctor / inspect     PASS
foundation check                   PASS
full Python suite                  PASS
mutation sensitivity              PASS
chassis fingerprint                PASS
TypeScript typecheck               PASS
frontend build                     PASS
real TS -> Python vertical         PASS
negative scope control             PASS
hosted final gates                 PASS
```

Reconciliation does **not** imply executor promotion.

---

## Core engineering rule

CodePro separates implementation, execution, verification, acceptance, and promotion.

```text
SCIENTIFIC_SIGNAL != LOCAL_PASS
HYPOTHESIS        != IMPLEMENTATION
IMPLEMENTATION    != EXECUTED
EXECUTED          != VERIFIED
VERIFIED          != ACCEPTED
ACCEPTED          != PROMOTED
```

Additional invariants:

```text
AVAILABILITY != QUALIFICATION
COMMAND_EXIT != TASK_SUCCESS
BLOCKED      != PASS
NOT_EXECUTED != PASS

NO_SILENT_FALLBACK
NO_SILENT_EXECUTOR_SWITCH
NO_SILENT_SCOPE_EXPANSION
```

---

## What is implemented

### Chassis contracts

- **P0** executor-agnostic execution contracts and telemetry;
- **P1** deterministic task characterization;
- **P2** deterministic progress/stagnation assessment;
- **P3** bounded rule-based routing and escalation contracts;
- **P4** repository planning/state artifacts;
- **P5** patch verification;
- **P6** handoff/context accounting.

### Research / evidence contracts

Frozen contracts exist for:

- Study Spec;
- Workload;
- Treatment;
- Measurement;
- Analysis;
- Validity;
- Promotion;
- Environment;
- Deviation;
- Failure Attribution;
- Run Provenance.

### Governance and execution boundaries

Implemented boundaries include:

- fail-closed deserialization/evidence semantics;
- command observation without task-status inference;
- request scope and permission authority;
- execution/time budgets;
- environment identity;
- executor qualification/binding;
- independent acceptance authority;
- non-overwriting persisted evidence;
- architecture/property/metamorphic/mutation-sensitivity checks;
- cross-version Python verification.

---

## Executor status

This section is deliberately explicit because these states are not equivalent.

### Qualification tooling present

Current `main` contains preserved/reconciled tooling for areas including:

- **mini-SWE-agent v2.4.6** provider-free qualification;
- mini-SWE runtime-access controls;
- verifier-control qualification;
- **Gemini CLI** executor qualification;
- **mini-SWE-agent + Gemini API** qualification;
- executor/runtime identity and capability qualification;
- related frozen task/verifier evidence paths.

These tools exist and are part of the engineering surface.

### What that does *not* mean

```text
QUALIFICATION_TOOL_EXISTS
!=
EXECUTOR_PROMOTED
```

and:

```text
RUNTIME_ACCESS_PASS
!=
TASK_SOLVING_PASS
!=
BENCHMARK_WIN
```

Provider-backed runners, credentials, or model calls are not executed merely because the tooling exists.

### Current promotion state

No hidden fallback, automatic ranking, or executor promotion is authorized from availability alone.

A concrete executor becomes bindable only when the **exact executor + adapter identity** has explicit qualification evidence for the requested capability.

Multiple equally qualified executors are blocked rather than silently ranked.

### Real-task evidence boundary

The project already has provider-free implementation/vertical validation and qualification infrastructure.

The next important evidence step is not another abstraction. It is **real, controlled task execution** with frozen:

- task/repository revision;
- executor identity;
- model/provider treatment;
- budget;
- environment;
- verifier;
- acceptance definition;
- instrumentation.

That is the boundary required before stronger product or comparative claims.

---

## Local runtime work

The project also contains a qualified **Windows-native llama.cpp runtime baseline** on the measured local hardware configuration.

That evidence establishes runtime compatibility and measured CPU/GPU smoke behavior.

It does **not** yet imply that the complete CodePro product path is using that runtime for task-solving.

The normal roadmap keeps these steps separate:

```text
runtime qualification
      ↓
telemetry baseline
      ↓
model compatibility
      ↓
CodePro -> local runtime plumbing
      ↓
execution + verifier plumbing
      ↓
scaffold comparison
```

### Phase 4 compatibility closure

The frozen compact-model pool completed local compatibility qualification:

```text
L1 Nanbeige4.2-3B   COMPATIBLE
L2 Qwen3.5-4B       COMPATIBLE
L3 Granite 4.2 3B   COMPATIBLE
L4 SWE-Dev-7B       COMPATIBLE (stretch)
```

This establishes compatibility, not model selection, ranking, routing, acceptance, or promotion.

Evidence: [Phase 4 compatibility audit](docs/audits/phase4-model-compatibility-20260928.md).

### Phase 5 local-runtime closure

The explicit local-runtime path passed a real frozen-runtime smoke.
CodePro -> loopback llama-server -> exact model alias -> response -> persisted telemetry/evidence.
Fallback remains disabled and HTTP, runtime, model, timeout, and protocol failures remain distinct.
Granite 4.2 3B is a Phase 5 plumbing fixture, not a selected or promoted product model.
Evidence: docs/audits/phase5-local-runtime-plumbing-20260928.md.

### Phase 6 execution/verifier closure

The generic execution/verifier plumbing passed a controlled isolated-worktree validation:

`CodePro -> controlled scaffold fixture -> isolated repository -> patch -> command/test -> independent verifier -> persisted final state/telemetry`.

The fixture is not a qualified scaffold and no model was invoked; Phase 7 owns real scaffold compatibility against the Phase 5 local runtime.

Evidence: [Phase 6 execution/verifier audit](docs/audits/phase6-execution-verifier-plumbing-20260928.md).

See [roadmap.md](roadmap.md).

---

## Minimal product path

```text
authorized request
      ↓
characterization
      ↓
explicit executor binding
      ↓
clean Git revision + scope
      ↓
execution
      ↓
raw observations
      ↓
declared verifier
      ↓
persisted evidence
      ↓
independent acceptance
```

No stage is allowed to silently acquire authority owned by a later stage.

---

## CLI

Install the current checkout:

```text
python -m pip install --no-deps -e .
```

Then:

```text
codepro --help
codepro --version
codepro doctor
codepro inspect
codepro inspect --json
codepro run --help
```

Equivalent module entrypoint:

```text
python -m arkx --help
```

The public product command is `codepro`. The Python implementation namespace remains `arkx` so introducing the CLI does not force an unrelated package-rename migration.

### `codepro inspect`

Observational only.

It may inspect:

- Git state;
- PATH;
- project markers;
- locally observable capabilities.

It does not promote an available executor to `QUALIFIED`.

### `codepro run`

The operational execution boundary requires:

- an exact clean Git revision;
- explicit scope/authority/budget;
- caller-supplied executor argv;
- declared verifier argv.

It uses:

- no shell interpretation;
- no automatic executor selection;
- no silent fallback;
- persisted non-overwriting evidence.

A process result remains an observation, not acceptance.

---

## Vertical implementation validation

A provider-free implementation validation runner exercises the minimal vertical path in a disposable repository.

```text
py -3.13 tools/run_vertical_implementation_validation.py
```

Expected classification:

```text
VERTICAL_IMPLEMENTATION_VALIDATED
```

This is **not** an M1 real-task pass.

The runner explicitly records:

```text
m1_real_task = NOT_EXECUTED
```

A real-task observation requires a separately authorized repository/task.

---

## M1 independent acceptance

After a real vertical produces the required verified evidence, acceptance is performed separately without re-executing the task:

```text
py -3.13 tools/accept_m1_doctor_json.py   --evidence-root <evidence-root>
```

Successful evidence review can produce:

```text
M1_INDEPENDENT_ACCEPTED
```

Acceptance writes a new non-overwriting evidence artifact.

It does not silently authorize release/promotion.

---

## Verification

From the repository root:

```text
PYTHONPATH=src python -m arkx.baseline
PYTHONPATH=src python -m unittest discover -s tests -t . -v
python tools/check_foundation.py
PYTHONPATH=src python tools/mutation_probe.py
PYTHONPATH=src python tools/chassis_fingerprint.py
```

CI verifies supported Python versions and the TypeScript/product surfaces.

The project also carries focused qualification/compatibility workflows. Their result must always be interpreted according to the exact scope they executed.

---

## Architecture boundary

```text
CodePro
├── docs/          contracts, decisions, audits, protocols
├── experiments/   bounded integrations and evidence surfaces
├── src/arkx/      authoritative Python chassis/core
├── src/chassis/   TypeScript product/API compatibility surfaces
├── tests/         executable verification boundary
└── tools/         qualification and reproducible validation
```

The current reconciled product avoids duplicate authority: product surfaces that need authoritative execution semantics are bound to the proven core rather than silently re-implementing task authority.

See [docs/architecture.md](docs/architecture.md).

---

## Current optimization target

```text
VERIFIED_CAPABILITY
────────────────────────
TOTAL_OPERATIONAL_COST
```

Operational cost includes more than money:

- tokens;
- latency;
- calls/retries;
- context;
- RAM/VRAM/compute;
- coordination;
- complexity;
- failure surface;
- maintenance burden.

The intended experimental sequence is:

```text
QUALIFY
-> RUN
-> MEASURE
-> REPLICATE
-> ABLATE
-> VALIDATE HELD-OUT
-> PRUNE
-> PROMOTE ONLY WHAT SURVIVES
```

Negative results are valid results. If a mechanism does not pay for itself, the correct outcome may be to remove it.

---

## Start here

- [Roadmap](roadmap.md)
- [Project contract](docs/project-contract.md)
- [Architecture boundary](docs/architecture.md)
- [Experimental protocol](docs/experimental-protocol.md)
- [Reconciliation roadmap](docs/reconciliation-roadmap.md)
- [R5 reconciliation audit](docs/audits/reconciliation-r5-20260927.md)

For agent/development work, read [AGENTS.md](AGENTS.md) before changing the repository.
