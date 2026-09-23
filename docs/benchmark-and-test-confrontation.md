# Confrontação do plano com testes e benchmarks

## Pergunta

Os testes locais e os benchmarks já registrados sustentam a direção de
fortalecer um núcleo executor-agnostic, separar execution/verification/
acceptance/promotion e preservar bloqueios como estados explícitos?

## Evidência de testes locais

Com `PYTHONPATH=src`:

| Evidência | Resultado | O que sustenta | O que não sustenta |
|---|---:|---|---|
| Testes P0–P7 e P8 determinísticos | 180 aprovados | contratos, serialização, invariantes e estados fail-closed | capacidade de executor ou provider |
| Testes de outcomes/orchestration/baseline/authority/promotion/harness | 75 aprovados | separação de outcomes, identidade de attempt, envelope de erro, manifest, replay, persistência atômica, lifecycle, presença de artefatos, consistência, leitura consolidada, indexação, comparabilidade, relatório de pares, preservação de métricas desconhecidas, autoridades independentes, gate de promotion, vínculo ao snapshot, binding, persistência da decisão e registro consolidado do experimento | execução real end-to-end |
| Teste OpenRouter adapter | bloqueado | dependência externa é explicitamente necessária | qualidade do adapter em ambiente ausente |
| Import público `arkx` | aprovado | pacote é importável com `PYTHONPATH=src` | instalação reproduzível de pacote |
| `pytest` | bloqueado | baseline de ambiente incompleto | resultado negativo do código |

Os testes sustentam a direção de contratos pequenos, estados explícitos e
decisões puras. Eles não sustentam uma afirmação de capability operacional.

## Evidência SWE-bench/Docker registrada

Os artifacts contêm execuções distintas para as mesmas tarefas:

| Grupo | Resultado observado | Interpretação válida |
|---|---|---|
| Docker runs 01–02 | `unresolved`, razão `missing_module` | falha de execução/ambiente da avaliação |
| Docker runs 03–04 | `resolved=1` | autoridade Docker conseguiu resolver as tarefas congeladas |
| Docker LF runs 01–02 | `resolved=1` | variante de ambiente também resolveu as tarefas |
| Qualification runs 03–04 | erro sem resultado de tarefa | qualification bloqueada/incompleta |
| Wave 0 Treatment A | `BLOCKED`, Docker daemon indisponível | nenhum model run foi executado |

Esses resultados não devem ser agregados como uma taxa única. Eles possuem
identidades de run, ambientes e estados diferentes. A variação entre
`missing_module`, `resolved` e erro confirma a necessidade de preservar:

- identidade completa do ambiente;
- executor authority separada da task result;
- falha de infraestrutura distinta de rejeição da tarefa;
- attempts não sobrescritos;
- replay e comparação somente entre controles compatíveis.

## Confrontação das hipóteses do plano

| Hipótese arquitetural | Evidência atual | Veredito |
|---|---|---|
| Outcomes devem ser neutros em relação ao executor | 75 testes passam após a extração e o contrato do harness | sustentada localmente |
| Acceptance não deve depender do runner | import dependency existia e foi removida dos módulos centrais | sustentada estruturalmente |
| Capability declarada não equivale a qualification | contratos P8.1 e testes preservam `UNKNOWN`/`BLOCKED` | sustentada localmente |
| Infra failure não deve virar task rejection | logs mostram Docker/provider failures separados | sustentada empiricamente |
| Fallback silencioso é perigoso | runs distintos possuem resultados e blockers diferentes | sustentada empiricamente |
| Um executor protocol neutro é necessário | runner atual importa mini/provider/sandbox indiretamente | sustentada por inspeção estrutural |
| Provider e sandbox precisam de boundaries próprias | OpenRouter, Git Bash e Docker têm falhas independentes | sustentada empiricamente |
| Arquitetura atual já é executor-agnostic | `p82_baseline` e SWE-bench ainda estão na API pública | falsificada pelo estado atual |

### Evidência incremental mais recente

Os blocos posteriores adicionaram contratos neutros de executor/provider/sandbox,
lifecycle, adapter do baseline, ponte de orquestração e `ExecutionPlan`. A
suíte focada atual relevante passou com 101 testes, incluindo a verificação de
que o plano é construído deterministicamente antes da invocação do executor e
que os caminhos neutro e legado permanecem compatíveis.

Isso fortalece a direção arquitetural, mas não altera a conclusão empírica:
trata-se de evidência local de contrato. A qualificação de provider, modelo,
executor, Docker, SWE-bench ou mecanismo continua dependente de execução externa
com identidade e artefatos preservados.
| O plano já pode ser validado com benchmark de capability | Wave 0 está bloqueado e resultados Gold são autoridade de avaliação | não demonstrada |
| Um novo executor deve ser escolhido agora | não há capability gap experimental comparável | rejeitada por insuficiência de evidência |

## Decisão

A direção do plano está correta como direção de engenharia e governança
experimental. A evidência não autoriza ainda:

- promover executor;
- escolher provider/modelo;
- afirmar eficácia de B1/C1/D1;
- usar SWE-bench Gold como benchmark de qualidade do Arkx;
- afirmar que o pipeline runtime está reproduzível end-to-end.

## Consequência para o plano

As Fases 0–4 devem continuar antes de qualquer novo experimento de mecanismo
ou comparação de executor. A Fase 5 deve adaptar o baseline somente depois que
`Executor`, `Provider`, `Sandbox`, lifecycle e artifact store tiverem contratos
testados com fakes.

## Critério para reabrir a questão de executor

A escolha de executor só pode ser reavaliada quando houver, para pelo menos uma
comparação controlada:

1. task sample congelado;
2. executor, provider, modelo, sandbox, versão e configuração identificados;
3. mesma verification e acceptance authority;
4. budgets equivalentes;
5. replicates suficientes para a hipótese declarada;
6. raw artifacts preservados;
7. estados de infraestrutura separados dos resultados de tarefa;
8. acceptance independente;
9. decisão explícita de promotion.

O bloco de capability registry elevou a suíte focada relevante para 104 testes
e adicionou uma forma determinística de comparar declarações de capacidade.
Isso reduz contratos implícitos, mas não é evidência de que a capacidade
declarada funciona em produção: essa distinção permanece explícita.

O bloco de budget adicionou digest estável para limites de execução e elevou a
suíte focada para 105 testes. Isso melhora a reprodutibilidade da identidade do
plano, mas não prova enforcement de budget nem comportamento de retry.

O bloco de retry transformou a decisão de nova tentativa em contrato explícito e
elevou a suíte focada para 107 testes. Isso reduz tratamento de erro implícito,
mas ainda não mede eficácia de retries em provider ou executor real.

O bloco de lineage adicionou identidade determinística para o próximo attempt e
elevou a suíte focada para 109 testes. Isso melhora replay e diagnóstico, mas
não demonstra eficácia de retry nem comportamento de provider real.

O bloco de artifact store elevou a suíte focada para 111 testes e passou a
persistir a cadeia de retry sem sobrescrita. Isso melhora replay e diagnóstico,
mas ainda não mede a eficácia do retry em infraestrutura real.

O bloco de replay elevou a suíte focada para 112 testes e passou a validar
lineage durante a leitura. Isso melhora auditoria e reproducibilidade, mas não
transforma artifacts históricos incompletos em evidência de retry.

O bloco de budget ledger elevou a suíte focada para 114 testes e demonstrou
consumo idempotente por attempt. Isso é evidência de contrato local, não prova
de enforcement distribuído ou de eficácia experimental.

O bloco de plan binding elevou a suíte focada para 115 testes e tornou o budget
parte explícita da identidade do plano. Isso melhora comparabilidade e replay,
mas ainda não prova enforcement durante execução real.

O bloco de persistência do ledger elevou a suíte focada para 116 testes e
registrou o uso no manifest com identidade verificável. Isso melhora auditoria,
mas não prova enforcement end-to-end em executor real.

O bloco de lifecycle budget-aware elevou a suíte focada para 118 testes e
demonstrou gating local da invocação. Isso não substitui validação de enforcement
em executor/provider reais.

O bloco de persistência atômica elevou a suíte focada para 119 testes e tornou o
manifest replayable. Isso não transforma a escrita em evidência de correção ou
aceitação da tarefa.

O bloco de event log elevou a suíte focada para 121 testes e tornou o lifecycle
replayable em JSONL. Isso fortalece diagnóstico e reproducibilidade, mas não
converte telemetria em evidência de correção ou acceptance.

O bloco de replay elevou a suíte focada para 123 testes e demonstrou
reconstrução determinística de fatos do lifecycle. Isso melhora reproducibilidade
sem fingir que replay é uma nova execução ou aceitação.

O bloco de consistência elevou a suíte focada para 124 testes e passou a detectar
divergência entre eventos e manifest. Isso fortalece auditoria, mas não produz
aceitação nem corrige artifacts inconsistentes.

O bloco de outcomes independentes elevou a suíte focada para 125 testes e
preservou a separação entre execução, verification e acceptance. Isso fortalece
o protocolo, mas não aceita nenhum patch por replay.

O bloco de replay completo elevou a suíte focada para 127 testes e explicitou a
cadeia entre os estágios. Isso melhora auditoria, mas não transforma referências
em evidência válida de promotion.

O bloco de classificação de referências elevou a suíte focada para 129 testes e
impediu que refs registradas fossem tratadas automaticamente como artifacts
válidos. Isso melhora reprodutibilidade e diagnóstico.

O bloco de inventário do attempt elevou a suíte focada para 130 testes e passou a
classificar refs contra artifacts validados. Isso melhora auditabilidade, mas
não cria artifacts ausentes nem promove resultados.

O bloco de integridade elevou a suíte focada para 131 testes e tornou explícita
a diferença entre cadeia completa, incompleta e inconsistente. Isso não é uma
decisão de acceptance ou promotion.

O bloco de recovery plan elevou a suíte focada para 137 testes e vinculou a ação
ao attempt de origem. Isso melhora replay e auditoria, mas não executa recovery
nem demonstra eficácia de escalonamento.

O bloco de recovery replay elevou a suíte focada para 138 testes e preservou
compatibilidade com runs sem recovery. Isso melhora auditabilidade sem afirmar
que o plano de recovery foi executado.

O bloco de identidade de recovery manteve a suíte focada em 138 testes e
eliminou referências ambíguas de plano. Isso fortalece replay, mas não mede
eficácia de recovery real.

O bloco de identidade de execução elevou a suíte focada para 139 testes e
fortaleceu o vínculo plan/attempt. Isso melhora replay, mas não aceita nenhum
resultado por referência.

O bloco de outcome references manteve a suíte focada em 139 testes e deu
identidade reprodutível aos resultados de verification e acceptance. Isso não
constitui gate de promotion.

O bloco de cadeia final manteve a suíte focada em 139 testes e validou o vínculo
entre outcomes e promotion. Isso não promove nenhum candidato nem substitui
evidência experimental.

A validação global alcançou 291 testes e permaneceu bloqueada apenas na
importação do adapter OpenRouter por dependência `minisweagent` ausente. Isso
confirma que a suíte focada local continua útil, mas a suíte completa ainda não
é evidência de integração externa qualificada.

O controle dependency-isolated passou com 290 testes. A diferença entre 290
testes verdes e a suíte completa bloqueada por um import foi preservada como
estado de infraestrutura, não convertida em sucesso de integração.

O Bloco A confirmou que a direção executor-agnostic está correta no núcleo, mas
os adapters externos ainda vazam `minisweagent`, Git Bash, Docker e SWE-bench
para a camada experimental. A matriz de readiness preserva esses blockers e
impede promoção por evidência histórica ou por testes locais.

O Bloco B fortaleceu a qualification boundary com identidade, dependências,
capabilities e evidência determinísticas. Os 293 testes isolados passaram, mas
isso não qualifica os adapters externos concretos.

O preflight concreto confirmou que presença de executável não equivale a
runtime utilizável: Git Bash foi classificado como `BLOCKED` por acesso negado e
Docker como `BLOCKED` por daemon inacessível. Essa distinção evita falsos
positivos de readiness.
