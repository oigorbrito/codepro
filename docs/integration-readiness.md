# Arkx — external integration readiness

Data da leitura: 2026-09-23  
Branch: `codex/auditoriaarquitetural`  
Python: `3.11.9`

## Regra de interpretação

`PASS` nesta matriz significa que o boundary ou preflight local foi observado.
Não significa qualificação de executor, provider, modelo ou benchmark. Logs
históricos são raw evidence e permanecem vinculados às identidades que
registraram; não são reutilizados como prova de uma configuração diferente.

## Readiness matrix

| Boundary | Estado atual | Evidência | Principal blocker | Decisão |
|---|---|---|---|---|
| `Executor` protocol | READY_FOR_FAKE_CONTRACT | 139 focused tests; fake executor lifecycle | integration identity absent | usable for contract work |
| `Provider` protocol | READY_FOR_FAKE_CONTRACT | provider request/response tests | no provider adapter in `src/arkx` | usable for contract work |
| `Sandbox` protocol | READY_FOR_FAKE_CONTRACT | fake sandbox tests | concrete sandbox remains external | usable for contract work |
| P8 baseline adapter | FUNCTIONAL_BUT_UNQUALIFIED | baseline adapter and artifact tests | real runner dependency/runtime | adapter may be tested, not promoted |
| OpenRouter adapter | BLOCKED | source in `tools/p82_openrouter_model.py`; historical raw logs | `minisweagent` import unavailable | no current qualification |
| Git Bash sandbox | BLOCKED | `bash.EXE` detected | Windows alias returned `E_ACCESSDENIED`; concrete adapter imports `minisweagent` | no sandbox qualification |
| Docker evaluator | BLOCKED | Docker CLI `29.7.2` present | daemon denied access to `dockerDesktopLinuxEngine` | no SWE-bench qualification |
| Ollama runtime | AVAILABLE_RUNTIME_ONLY | Ollama `0.34.3` detected; prior local logs exist | model/config/adapter identity not frozen in current run | not provider-qualified |
| SWE-bench authority | RECORDED_EXTERNAL_AUTHORITY | existing Gold records under `logs/evaluation/` | authority result does not qualify mechanism/provider | authority only |
| full test suite | PASS_LOCAL | 298 tests pass, including adapter import boundaries | concrete runtimes remain unavailable or unidentified | no external qualification claim |

## Boundary leakage

- `src/arkx` exposes neutral `Executor`, `Provider`, and `Sandbox` protocols.
- `tools/p82_openrouter_model.py` directly subclasses
  `minisweagent.models.openrouter_model.OpenRouterModel`.
- `tools/p82_bash_environment.py` directly subclasses
  `minisweagent.environments.local.LocalEnvironment`.
- P8 runner and OpenRouter/Bash adapters therefore remain integration modules,
  not neutral core implementations.
- Docker and SWE-bench appear in the experimental authority/evaluation path,
  not as generic execution contracts.

## Acceptance decision

The neutral contract layer is ready for isolated fake-based development. The
external integration layer is not ready for promotion or comparative claims.
The next implementation should add adapter-level preflight records and
capability identity, not a fallback executor.

## Preflight contract

The core contract is now implemented in `src/arkx/integration.py`:

- `AdapterIdentity` binds kind, name, version, and configuration;
- `DependencyObservation` preserves available, unavailable, and unknown;
- `AdapterPreflight` records capabilities, evidence, and reason;
- `assess_preflight` emits `READY`, `BLOCKED`, `UNKNOWN`, or `FAILED` without
  loading a concrete adapter.

The dependency-isolated suite passed with 298 tests. This is contract evidence;
the concrete OpenRouter, Git Bash, Docker, and SWE-bench boundaries remain in
their previously recorded states.

The concrete read-only collector is `tools/collect_adapter_preflight.py`.
Its current raw result is recorded in
`logs/architecture/concrete-adapter-preflight-20260923.json`. It distinguishes
executable presence from successful runtime access; Git Bash is therefore
`BLOCKED`, not ready.

The adapter modules are now import-safe but execution-strict: absence of
`minisweagent` no longer prevents test discovery, while construction still
raises an explicit runtime boundary error. This changes local testability, not
external readiness.
