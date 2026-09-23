# Reproducibility baseline — 2026-09-23

## Scope

This record describes the local deterministic-test baseline before the next
architecture slice. It is environment evidence, not executor qualification.

## Repository identity

| Field | Value |
|---|---|
| Branch | `codex/auditoriaarquitetural` |
| HEAD | `aef1df4d33c95c522dfda8f2e21f9bd09eb6ce6b` |
| OS | Windows |
| Python | 3.11.9 |
| Git | 2.55.0.windows.5 |
| Source import mode | `PYTHONPATH=src` |

The working tree contains pre-existing modified and untracked files. This
baseline does not claim that the tree is clean or that those changes belong to
this phase.

## Commands

Core import smoke test:

```powershell
$env:PYTHONPATH = "src"
python -c "import arkx; print('ok', len(arkx.__all__))"
```

Deterministic test command currently available:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -p 'test_*.py'
```

## Observed result

- Core import: `PASS` (`151` public names exposed at the time of recording).
- Focused core/outcome/orchestration/baseline/authority/promotion/harness tests: `PASS`, 75 tests.

The second architecture block adds executor/provider/sandbox contract tests;
its focused evidence is recorded in
`logs/architecture/execution-contract-block-20260923.json` with 79 passing
tests. This remains local contract evidence, not executor qualification.

The third architecture block adds the fake contract lifecycle; its focused
evidence is recorded in
`logs/architecture/contract-lifecycle-block-20260923.json` with 82 passing
tests. No real executor or provider was invoked.

The fourth architecture block adds the P8.2 baseline adapter; its focused
evidence is recorded in
`logs/architecture/baseline-executor-adapter-block-20260923.json` with 84
passing tests. This is adapter evidence, not executor qualification.

The fifth architecture block adds the orchestration bridge; its focused
evidence is recorded in
`logs/architecture/contract-orchestration-bridge-block-20260923.json` with 92
passing tests. Verification, acceptance and promotion remain outside the
executor.

The seventh architecture block centralizes the legacy result boundary; its
focused evidence is recorded in
`logs/architecture/legacy-result-boundary-block-20260923.json` with 95
passing tests. The legacy API remains for compatibility.

The eighth architecture block corrects the public result collision; its
focused evidence is recorded in
`logs/architecture/public-result-boundary-block-20260923.json` with 96
passing tests.

The tenth architecture block adds `ExecutionPlan`; its focused evidence is
recorded in `logs/architecture/execution-plan-block-20260923.json` with 100
passing tests. Plan construction invoked no executor or provider.

The ninth architecture block adds a static legacy-consumer boundary test; its
focused evidence is recorded in
`logs/architecture/legacy-consumer-boundary-block-20260923.json` with 98
passing tests.

The sixth architecture block adds direct neutral-executor orchestration; its
focused evidence is recorded in
`logs/architecture/direct-neutral-orchestration-block-20260923.json` with 94
passing tests. Direct and bridged paths were equivalent under fakes.
- Full unittest discovery: `BLOCKED` by missing `minisweagent` in
  `test_p82_openrouter_adapter`; the current discovery reached 205 tests
  before the import error.
- `pytest`: `BLOCKED`; package is not installed in the selected environment.
- `minisweagent`: `BLOCKED`; import unavailable.
- Docker server: `BLOCKED`; Docker daemon unavailable through the configured
  named pipe.

## Interpretation

The passing tests are local deterministic evidence only. They do not qualify
an executor, provider, model, Docker environment, SWE-bench path, or treatment.

The missing dependencies are preserved as infrastructure blockers. No fallback
executor, provider, test runner, or local evaluator was selected.

## Acceptance state

`F0_BASELINE = BLOCKED_FOR_EXTERNAL_INTEGRATIONS`

The focused evidence for the harness contract slice is recorded in
`logs/architecture/harness-contract-slice-20260923.json`.

The core import and deterministic tests are usable for continuing contract
work. External adapter qualification remains unavailable until the missing
runtime identities and dependencies are explicitly restored.

The eleventh architecture block integrates `ExecutionPlan` into the routed
orchestration boundary. Its focused evidence is recorded in
`logs/architecture/orchestration-execution-plan-block-20260923.json` with 101
passing tests. Equivalent authorized inputs produced equal plans, the plan was
available on orchestration results, and neutral/legacy executor paths remained
compatible. This remains local contract evidence; no external executor,
provider, model, Docker environment, or SWE-bench authority was qualified.

O bloco seguinte adiciona `CapabilityProfile` e `CapabilityRegistry` para
registrar identidade, versão, configuração, capacidades e referências de
evidência de componentes. A suíte focada passou com 104 testes. O registro é
descritivo e determinístico; não faz descoberta dinâmica, fallback ou
qualificação de provider/modelo.

O bloco de budget adiciona `ExecutionBudgetSpec`, com limites neutros e digest
estável para identidade de plano/manifest. A suíte focada passou com 105 testes.
O bloco não consome budget nem implementa retry, escalonamento ou reconciliação
com os budgets de routing, recovery, qualification e request.

O bloco de artifact store integrou a reserva explícita ao lineage. A suíte
focada passou com 111 testes; a operação persiste `retry-lineage.json`, rejeita
duplicidade e drift de identidade, e não executa o executor.

O bloco de replay integrou `RetryLineage` ao `AttemptSnapshot`. A suíte focada
passou com 112 testes; lineage presente é validada contra o manifest, enquanto
artifacts históricos sem lineage continuam legíveis com ausência explícita.

O bloco de retry adiciona `RetryPolicy` e `RetryDecision` como autorização pura.
A suíte focada passou com 107 testes, cobrindo erro retryable, erro unknown,
domínio não permitido e esgotamento de política/budget. Nenhum retry automático
foi executado; recovery e execução continuam sendo fronteiras separadas.

O bloco de lineage adiciona `RetryAttemptPlan`, que deriva deterministicamente
o próximo `attempt_id`, preserva o attempt anterior e não reserva nem sobrescreve
artefatos. A suíte focada passou com 109 testes. A reserva efetiva no artifact
store continua uma operação explícita posterior.

O bloco de budget ledger adiciona consumo imutável por `attempt_id`. A suíte
focada passou com 114 testes; consumo repetido retorna `ALREADY_CONSUMED` sem
duplicar uso e rejeições preservam o ledger. A reconciliação dos budgets de
outras camadas continua pendente.

O bloco de binding integra `ExecutionBudgetSpec` ao `ExecutionPlan`. A suíte
focada passou com 115 testes; o plano deriva ou valida o digest e a
orquestração preserva o vínculo. O ledger ainda não é consumido por execução
real.

O bloco seguinte persiste o `BudgetLedger` no `RunManifest`, vinculado ao
`attempt_id` e ao digest do plano. A suíte focada passou com 116 testes; drift de
attempt ou digest é rejeitado e o manifest continua imutável. Enforcement
end-to-end no executor permanece pendente.

O bloco seguinte adiciona escrita atômica do `RunManifest` validado no
`ArtifactStore`. A suíte focada passou com 119 testes; identidade e lifecycle
são validados antes da persistência e o manifest pode ser recarregado. Escrita
bem-sucedida não implica verification ou acceptance.

O bloco de lifecycle budget-aware passou com 118 testes. O ledger é consumido
antes da invocação; budget aceito chama o fake executor uma vez, enquanto budget
excedido produz `BLOCKED` estruturado sem chamada. Persistência de manifest e
execução externa continuam separadas.

O bloco de event log adiciona persistência JSONL determinística para eventos de
lifecycle. A suíte focada passou com 121 testes; `run_id` e monotonicidade
temporal são validados na escrita e leitura. O log permanece telemetria, não
decisão de acceptance.

O bloco de replay adiciona `ReplayState` e `replay_events` como redução pura do
event log. A suíte focada passou com 123 testes; fatos declarados são
reconstruídos sem executor, verifier ou inferência de acceptance.

O bloco de consistência compara replay e `RunManifest`. A suíte focada passou
com 124 testes; identidade divergente e status conflitante são rejeitados, sem
reparo automático ou inferência de estado ausente.

O bloco seguinte preserva verification e acceptance separadamente no replay. A
suíte focada passou com 125 testes; conflitos com evidência independente são
rejeitados e nenhum outcome é derivado de `COMPLETED`.

O bloco seguinte adiciona `ReplayChain` para referências explícitas de request,
plan, execution, verification, acceptance e promotion. A suíte focada passou
com 127 testes; ordem causal inválida é rejeitada e estágios ausentes não são
preenchidos.

O bloco de integridade adiciona `ChainIntegrity` com estados `COMPLETE`,
`INCOMPLETE` e `INCONSISTENT`. A suíte focada passou com 131 testes; a
classificação é apenas pré-condição e não executa acceptance ou promotion.

O bloco seguinte classifica referências do replay como `PRESENT`, `MISSING` ou
`INDETERMINATE`. A suíte focada passou com 129 testes; sem inventário físico, a
referência permanece indeterminada e não é convertida em sucesso.

O bloco seguinte conecta a classificação ao inventário validado do
`AttemptSnapshot`. A suíte focada passou com 130 testes; artifacts presentes e
refs ausentes são distinguidos sem varrer diretórios arbitrários ou substituir
artifacts.

O bloco seguinte adiciona `RecoveryPlan` determinístico e vinculado ao attempt
de origem. A suíte focada passou com 137 testes; o plano registra decisão e
target sem executar recovery ou trocar executor.

O bloco de recovery replay adiciona `recovery_ref` opcional à cadeia. A suíte
focada passou com 138 testes; a ordem causal é validada sem tornar recovery
obrigatório e sem quebrar consumidores posicionais legados.

O bloco seguinte vincula `recovery_ref` ao `RecoveryPlan.reference` canônico. A
suíte focada permanece com 138 testes; referência divergente é rejeitada sem
executar recovery.

O bloco de execução adiciona referências canônicas `plan://` e `execution://`.
A suíte focada passou com 139 testes; drift de plano ou attempt é rejeitado sem
inferir verification ou acceptance.

O bloco seguinte adiciona referências canônicas para `VerificationResult` e
`AcceptanceResult`. A suíte focada permanece com 139 testes; namespaces são
distintos e drift de referência é rejeitado sem promotion.

O bloco final de lineage adiciona referência canônica à `PromotionDecision` e
validação da cadeia de outcomes. A suíte focada permanece com 139 testes;
attempt, promotion ou acceptance divergentes são rejeitados sem executar
promotion.

O bloco de validação global executou a descoberta completa e alcançou 291
testes, mas ficou `BLOCKED` ao importar `test_p82_openrouter_adapter` por
ausência de `minisweagent`. O bloqueio foi preservado como dependência externa;
nenhum fallback foi selecionado e não foi classificado como falha funcional.

Como controle, a suíte foi executada excluindo somente o módulo bloqueado e
passou com 290 testes. Isso é evidência ampla de regressão local, mas não
qualifica a integração OpenRouter/minisweagent nem o executor externo.

O Bloco A de readiness consolidou adapters, dependências e preflights em
`docs/integration-readiness.md`. A conclusão é assimétrica: contratos neutros
estão prontos para desenvolvimento com fakes; OpenRouter, Git Bash, Docker e
SWE-bench permanecem bloqueados ou limitados à autoridade já registrada.

O Bloco B adiciona o contrato comum de preflight para adapters. A suíte isolada
passou com 293 testes; `READY`, `BLOCKED`, `UNKNOWN` e `FAILED` permanecem
distintos e nenhum fallback é selecionado.

O coletor concreto do Bloco B registrou OpenRouter, Git Bash e Docker como
`BLOCKED`, e Ollama como `UNKNOWN` por identidade/configuração não congelada. A
evidência raw está em
`logs/architecture/concrete-adapter-preflight-20260923.json`.
