# CodePro

CodePro is an executor-agnostic software-engineering chassis for running, measuring, verifying, and qualifying coding workflows through explicit authority boundaries and reproducible evidence.

> **MINIMUM SUFFICIENT ARCHITECTURE**  
> **FOR MAXIMUM RELIABLE CAPABILITY**

The project is local-first, evidence-driven, and fail-closed. A capability is not promoted because it exists or because one run succeeded.

```text
IMPLEMENTED != QUALIFIED
AVAILABLE != QUALIFIED
EXECUTED != VERIFIED
VERIFIED != ACCEPTED
ACCEPTED != PROMOTED
UNKNOWN != ZERO
INFRA_FAILURE != MODEL_FAILURE
```

No fallback, executor switch, scope expansion, or promotion may be silent.

## Architecture

The reconciled product has one authoritative execution core and a preserved React/Express product surface.

```text
React / Vite dashboard
        |
        v
Express API
        |
        +--> inspection / UI compatibility surfaces
        |
        +--> non-authoritative preview surfaces
        |      characterization
        |      progress
        |      routing
        |      M1 acceptance preview
        |
        v
TypeScript execution adapter
        |
        | explicit CODEPRO_PYTHON
        | explicit CODEPRO_EVIDENCE_DIR
        | shell = false
        v
python -m arkx run
        |
        v
authoritative Python core
        |
        +--> Git revision / clean-worktree checks
        +--> explicit authority and scope
        +--> bounded executor invocation
        +--> observed changed-file capture
        +--> verifier execution
        +--> evidence persistence
        +--> independent acceptance boundaries
```

The Python package under `src/arkx/` is the canonical semantic boundary for characterization, progress, routing, execution, verification, evidence, governance, qualification, and acceptance.

The TypeScript product surface is retained where useful, but duplicate semantic surfaces are explicitly marked `NON_AUTHORITATIVE_PREVIEW` rather than becoming a second source of truth.

## Current implemented capability

### Authoritative core

Implemented and covered by the repository test suite:

- installable `codepro` CLI on Python 3.12+;
- deterministic project inspection;
- task characterization contracts;
- progress/stagnation assessment;
- routing contracts and explicit escalation semantics;
- planning, composition, orchestration, governance, and request authority;
- bounded process execution with timeout and environment-failure separation;
- exact Git revision and clean-worktree enforcement;
- observed diff and changed-file scope validation;
- independent verifier execution;
- non-overwriting evidence persistence;
- provenance, event log, measurement, telemetry, and run-manifest contracts;
- executor qualification and promotion boundaries;
- independent acceptance records;
- fail-closed parsing and deserialization;
- architecture, property, metamorphic, mutation-sensitivity, and cross-version verification.

### React / Express dashboard

The React/Vite/Tailwind dashboard and Express server are intentionally preserved.

They provide useful product interaction for:

- runtime/doctor state;
- project inspection;
- characterization/progress/routing previews;
- real vertical execution;
- persisted run evidence;
- M1 acceptance preview;
- experiment fixtures and decision-basis helpers.

The dashboard is a product/control surface, not an independent authority boundary.

In particular:

```text
TypeScript characterization -> NON_AUTHORITATIVE_PREVIEW
TypeScript progress         -> NON_AUTHORITATIVE_PREVIEW
TypeScript routing          -> NON_AUTHORITATIVE_PREVIEW
TypeScript M1 review        -> WOULD_ACCEPT / WOULD_REJECT
```

Authoritative acceptance remains in the Python evidence boundary.

## Real execution vertical

The authoritative product path is no longer simulated:

```text
React / Express
-> src/chassis/vertical.ts
-> explicit CODEPRO_PYTHON
-> python -m arkx run
-> src/arkx/vertical.py
-> real Git state
-> caller-supplied executor argv
-> observed changed files
-> declared verifier argv
-> persisted result.json
```

The adapter does not silently choose an executor, expand scope, substitute a provider, or manufacture verifier success.

A positive control must reach `VERIFIED` from actual repository state and actual verifier evidence. A scope-negative control must fail closed when files outside the authorized scope are changed.

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

Important CLI detail:

```text
codepro doctor          # supported
codepro doctor --json   # not a supported contract
codepro inspect --json  # supported
```

`codepro inspect` is observational. It may inspect filesystem markers, PATH, and read-only Git state.

`codepro run` is the minimal authoritative execution surface. It requires explicit workspace/revision, authority, scope, budget, executor argv, verifier argv, and evidence location. It performs no automatic executor selection or fallback.

## Running the dashboard

Node 22 is the current hosted validation baseline.

Install dependencies:

```text
npm install
```

The Express product surface requires an explicit Python execution-core binding and evidence directory.

Windows PowerShell example:

```powershell
$env:CODEPRO_PYTHON = (py -3.14 -c "import sys; print(sys.executable)")
$env:CODEPRO_EVIDENCE_DIR = "$env:TEMP\codepro-evidence"

npm run dev
```

Available scripts:

```text
npm run dev
npm run start
npm run lint
npm run build
```

By default the server listens on port `3000`.

## Telemetry and evidence

CodePro separates generic execution telemetry from specialized local-inference measurement records.

The reconciled boundary preserves:

- execution identity and correlation;
- model/runtime/artifact identity;
- quantization and inference configuration;
- wall time;
- prompt and generation throughput;
- RAM and VRAM observations;
- GPU offload information;
- termination and exit-code semantics;
- raw evidence references;
- provenance and hashes;
- event sequence and decision history.

Missing observations remain unknown rather than being converted to zero.

## Qualified local runtime baseline

The current Windows-native local runtime baseline is based on:

```text
runtime           = llama.cpp b11205
upstream commit   = 95887577ab5fead779581a7030a83c7752ff3234
platform          = Windows x64
backend           = CUDA 13.4
GPU               = NVIDIA GeForce GTX 1650 4 GB
model             = ggml-org/gemma-3-1b-it-GGUF:Q4_K_M
```

Recorded controlled smoke measurements include:

| Metric | CPU | GPU offload |
| --- | ---: | ---: |
| Prompt throughput | 48.3 t/s | 74.6 t/s |
| Generation throughput | 16.8 t/s | 63.7 t/s |
| Wall time | 4335 ms | 3982 ms |
| Peak process RAM | 1135.6 MiB | 1214.9 MiB |
| GPU layers | — | 27/27 |
| VRAM delta | — | 906 MiB |

These values are qualification/smoke evidence, not a statistical benchmark or a universal performance claim.

## Executor and provider integrations

Executor/provider work is preserved as qualification capability without silently turning it into product routing or promotion.

Current repository assets include:

- Gemini CLI executor qualification;
- mini-SWE-agent v2.4.6 executor qualification;
- mini-SWE-agent v2.4.6 + Gemini API qualification;
- provider-free mini-SWE runtime-access controls;
- SWE-bench 5.0.2 verifier controls;
- bounded timeout, budget, trajectory/prediction, runtime-access, and verification checks.

The frozen mini-SWE-agent qualification identity is:

```text
version = v2.4.6
commit  = a83fcae82d2a08f0ee0c688f9d137b3566c097f8
```

These integrations do **not** imply that any executor is selected, ranked, promoted, or used as a silent fallback.

```text
AVAILABLE != QUALIFIED
QUALIFIED != SELECTED_BY_RANK
QUALIFIED != PROMOTED
```

Provider credentials are not required for the provider-free foundation and reconciliation gates.

## Verification

Python foundation:

```text
python tools/check_foundation.py
PYTHONPATH=src python -m arkx.baseline
PYTHONPATH=src python -m unittest discover -s tests -t . -p "test_*.py" -v
PYTHONPATH=src python tools/mutation_probe.py
PYTHONPATH=src python tools/chassis_fingerprint.py
python -m compileall -q src tests tools
```

TypeScript/frontend:

```text
npm run lint
./node_modules/.bin/tsx tools/check-telemetry.ts
npm run build
```

Real composed vertical:

```text
./node_modules/.bin/tsx tools/check-r5-composed-vertical.ts
```

The hosted CI currently validates the Python foundation across Python 3.12, 3.13, and 3.14, the TypeScript telemetry contract, frontend build, provider-safety boundary, and the real TypeScript-to-Python vertical.

## M1 independent acceptance

Authoritative M1 acceptance consumes persisted evidence without re-running the task.

Example:

```text
py -3.13 tools/accept_m1_doctor_json.py --evidence-root D:\projetos\codepro-m1-evidence
```

Successful classification:

```text
M1_INDEPENDENT_ACCEPTED
```

Acceptance writes a separate non-overwriting record and does not imply executor promotion or release authorization.

## Development posture

Every capability follows an evidence chain:

```text
HYPOTHESIS
-> IMPLEMENT
-> TEST
-> CAPTURE EVIDENCE
-> VERIFY
-> ACCEPT IF AUTHORIZED
-> PROMOTE ONLY IF JUSTIFIED
```

Primary optimization target:

```text
VERIFIED CAPABILITY / TOTAL OPERATIONAL COST
```

Operational cost includes money, provider/API calls, tokens, latency, retries, context, RAM/VRAM, compute, complexity, maintenance burden, and failure surface.

## Project status

The repository has completed the R1-R4 reconciliation tranches and the local/hosted R5 technical gates. The final authoritative execution pointer is maintained in:

- [roadmap.md](roadmap.md) — canonical operational roadmap;
- [docs/reconciliation-roadmap.md](docs/reconciliation-roadmap.md) — reconciliation control record;
- [docs/audits/reconciliation-r5-20260927.md](docs/audits/reconciliation-r5-20260927.md) — composed R5 evidence.

Do not infer promotion or future-phase completion from this README; the roadmap and recorded evidence are authoritative.

## Design and protocol references

- [Project contract](docs/project-contract.md)
- [Architecture boundary](docs/architecture.md)
- [Experimental protocol](docs/experimental-protocol.md)
- [Operational roadmap](roadmap.md)
- [Reconciliation roadmap](docs/reconciliation-roadmap.md)

