# Plano de fortalecimento arquitetural do Arkx

## Objetivo

Fortalecer o núcleo do Arkx para que ele seja executor-agnostic, reproduzível
e evolua independentemente de mini-SWE-agent, Nemotron, NOOA, SWE-agent ou
qualquer outro executor.

O plano não tem como objetivo escolher executor. O objetivo é criar boundaries
que permitam conectar, medir, comparar, aceitar, promover ou remover executores
sem alterar request, routing, verification, acceptance e promotion.

## Princípios de decisão

Toda mudança deve satisfazer simultaneamente:

```text
CONTRATO EXPLÍCITO
AND
TESTE EXECUTÁVEL
AND
EVIDÊNCIA REPRODUZÍVEL
AND
ACEITAÇÃO INDEPENDENTE
```

As seguintes distinções são obrigatórias:

```text
IMPLEMENTAÇÃO != EXECUÇÃO
EXECUÇÃO != VERIFICATION
VERIFICATION != ACCEPTANCE
ACCEPTANCE != PROMOTION
LOCAL PASS != EXPERIMENTAL EVIDENCE
BLOCKED != PASS
UNKNOWN != PASS
```

## Estado inicial conhecido

- O núcleo P0–P7 possui contratos determinísticos e testes unitários fortes.
- P8.2/P8.2a adicionam execução real, mas ainda acoplam o baseline a
  mini-SWE-agent, provider, subprocess, Git Bash e SWE-bench.
- Os outcomes de verification/acceptance já foram extraídos para um módulo
  neutro; `p82_baseline` mantém reexports temporários.
- A autoridade SWE-bench Docker possui evidência `resolved: true` para tarefas
  Gold congeladas.
- O Wave 0 Treatment A está bloqueado por indisponibilidade do Docker daemon.
- O ambiente atual não possui `pytest` nem `minisweagent` instalados; testes
  core requerem `PYTHONPATH=src`.

Esses fatos são baseline da auditoria, não justificativa para adoção de
executor.

## Confrontação com a decisão 0012

A decisão [0012](decisions/0012-evidence-routed-treatment-architecture.md)
continua sendo a referência estratégica: rotear por tratamento/capability,
executar depois da seleção, verificar antes de aceitar e exigir evidência antes
de promover.

Ela não substitui os contratos técnicos deste plano. Em particular:

1. `ROUTE BY REQUIRED CAPABILITY` precisa de um capability contract versionado,
   não somente de nomes de tratamento ou strings no registry.
2. `SUFFICIENT EXECUTOR` precisa ser uma decisão sobre um executor capaz de
   executar o contrato, não apenas sobre metadata qualificada.
3. A separação entre P8.2, P8.3 e P8.4 é uma ordem experimental; não autoriza
   o núcleo a importar os componentes concretos dessas fases.
4. A afirmação retrospectiva de complementaridade entre executores só pode ser
   usada como evidência normativa depois que seus dados brutos e identidade
   experimental forem localizados e reproduzíveis no repositório ou em uma
   autoridade referenciada.

Assim, a decisão 0012 permanece válida como hipótese arquitetural e princípio
de desenho. Os números retrospectivos que não possuem rastreabilidade local
devem permanecer como `UNVERIFIED` para fins de promoção.

## Ordem de execução

### Fase 0 — Controle do trabalho e baseline

Responsabilidade: tornar o estado de desenvolvimento e teste reproduzível.

Entregáveis:

- comando documentado para instalar/importar o pacote;
- comando de teste determinístico;
- relatório de baseline com branch, HEAD, ambiente e dependências;
- separação entre arquivos de trabalho, fixtures e artifacts de execução;
- teste mínimo de import público.

Hipótese falsificável:

> Um ambiente documentado consegue importar o pacote e executar todos os
> testes determinísticos sem depender de configuração manual implícita.

Critérios de aceitação:

- ambiente limpo reproduz o mesmo resultado;
- falhas de dependência aparecem como bloqueio explícito;
- nenhuma execução seleciona fallback silencioso;
- o conjunto de testes não grava artifacts de experimento no repositório.

### Fase 1 — Núcleo de outcomes e erros

Responsabilidade: remover dependências de P8.2 das fronteiras centrais.

Entregáveis:

- outcomes neutros de verification e acceptance;
- error envelope comum;
- códigos de erro com domínio, origem, severidade e retryability;
- compatibilidade temporária com imports legados.

Hipótese:

> Acceptance, promotion e orchestration podem operar sem importar qualquer
> runner ou adapter experimental.

Critérios:

- análise estática confirma ausência de imports proibidos;
- testes preservam serialização e estados existentes;
- erros de provider, executor, sandbox, verification e policy mantêm origem;
- `BLOCKED`, `UNKNOWN` e `NOT_EXECUTED` não são convertidos em sucesso.

Progresso verificável: outcomes neutros foram extraídos para `arkx.outcomes`
e `arkx.harness` agora define `RunManifest`, `ErrorEnvelope` e identidade
determinística de attempt. Os testes focados passam; a integração do adapter
OpenRouter permanece bloqueada pela dependência externa ausente. A fase
continua aberta até a migração controlada de um runner e o teste de replay.

### Fase 2 — Contratos de execução

Responsabilidade: definir interfaces neutras, sem implementar outro executor.

Entregáveis:

- `Executor` protocol;
- `Provider` protocol;
- `Sandbox` protocol;
- `ExecutionRequest`;
- `ExecutionResult`;
- `ExecutionArtifact` genérico;
- capability descriptors versionados.

Hipótese:

> Um fake executor determinístico pode percorrer o fluxo completo sem que o
> núcleo conheça mini-SWE-agent, OpenRouter, Docker ou SWE-bench.

Critérios:

- fake executor cobre completed, failed, blocked, timeout e not executed;
- núcleo não importa SDK, subprocess ou Docker;
- capabilities declaradas não são tratadas como qualification empírica;
- provider e sandbox podem ser substituídos por fakes.

Bloco 2 concluído com evidência local: `Executor`, `Provider`, `Sandbox`,
requests/results e fakes determinísticos foram adicionados. A integração do
runner P8.2 real ainda não foi feita e nenhum executor/provider foi promovido.

Bloco 3 concluído com evidência local: `ContractRun` percorre lifecycle fake
completo e mantém verification/acceptance como attachments independentes.

Bloco 5 concluído com evidência local: orchestration consome o protocolo
`Executor` através de uma ponte explícita, sem mover verification, acceptance
ou promotion para o executor.

Bloco 6 concluído com evidência local: a entrypoint de orchestration aceita o
protocolo neutro diretamente e preserva equivalência comportamental com a
ponte legada.

Bloco 8 concluído com evidência local: `arkx.ExecutionResult` agora aponta
para o contrato neutro e o resultado legado possui nome público distinto.

Bloco 9 concluído com evidência local: um teste de arquitetura impede novos
imports do resultado legado fora da camada de compatibilidade.

Bloco 10 concluído com evidência local: `ExecutionPlan` separa intenção
congelada de execução de `ExecutionResult` e produz requests sem efeitos
externos.

### Fase 3 — Lifecycle, plan e budgets

Responsabilidade: transformar estados dispersos em fluxo persistível e
verificável.

Entregáveis:

- task lifecycle state machine;
- execution plan;
- budget manager;
- retry policy;
- recovery planner;
- transições válidas e inválidas documentadas.

Hipótese:

> Um fluxo interrompido pode ser retomado ou bloqueado de forma determinística
> sem repetir etapas já confirmadas e sem ultrapassar budgets.

Critérios:

- cada transição possui teste positivo e negativo;
- retryable e non-retryable são distinguíveis;
- budgets são consumidos uma única vez por attempt;
- recovery não troca executor nem expande escopo silenciosamente;
- replay do mesmo input produz o mesmo plano e identidade.

### Fase 4 — Artifact store, trace e replay

Responsabilidade: tornar a execução auditável e reproduzível.

Entregáveis:

- `ArtifactStore` local;
- manifests e checksums;
- lineage request → plan → execution → verification → acceptance;
- event log persistente;
- trace/replay contract;
- writes atômicos e attempts imutáveis.

Hipótese:

> Toda decisão material pode ser reconstruída a partir de artifacts persistidos
> sem depender de memória do processo ou logs informais.

Critérios:

- artifact parcial não é apresentado como completo;
- dois runs equivalentes compartilham identidade estável;
- artifacts divergentes produzem identidade divergente;
- replay preserva decisões e estados, mas não finge reexecução;
- falhas mantêm raw output suficiente para diagnóstico.

### Fase 5 — Adaptação do baseline experimental

Responsabilidade: adaptar mini-SWE-agent ao novo boundary, sem promovê-lo.

Entregáveis:

- adapter do runner atual para `Executor`;
- adapter OpenRouter para `Provider`;
- Git Bash/local/Docker atrás de `Sandbox`;
- SWE-bench atrás de `Evaluator`/`AcceptanceAuthority`;
- preservação dos artifacts atuais.

Hipótese:

> O baseline atual pode ser conectado aos contratos neutros sem alterar seus
> resultados observados nem fazer o núcleo depender dele.

Critérios:

- os artifacts atuais continuam legíveis;
- provider failure, executor failure e sandbox failure permanecem distintos;
- não há fallback implícito;
- testes com fake adapters passam sem dependências externas;
- testes de integração externa são marcados como bloqueados quando faltarem
  Docker, provider, modelo ou pacote.

### Fase 6 — Verificação empírica dos tratamentos

Responsabilidade: somente depois das fases anteriores, executar experimentos.

Entregáveis:

- protocolo congelado;
- task sample congelado;
- identidade completa de executor/provider/model/sandbox/config;
- replicates serializados;
- raw evidence;
- acceptance independente;
- decisão de promotion separada.

Hipóteses possíveis:

- B1 melhora tarefas localizadas sob o mesmo executor;
- C1 melhora localização sem aumentar desnecessariamente o escopo;
- D1 apresenta interação entre B1 e C1;
- outro executor possui capability gap comprovado contra o baseline.

Nenhuma dessas hipóteses deve ser assumida como verdadeira antes da execução.

Critérios:

- controles divergentes são `INCOMPARABLE`;
- identidade ausente é `UNKNOWN` ou `BLOCKED`;
- falha de infraestrutura não é rejeição da tarefa;
- resultado experimental não promove automaticamente componente algum.

## Gate de engenharia de software

Antes de aceitar cada fase, revisar:

- responsabilidade única;
- API pública mínima;
- dependências acíclicas e direcionais;
- invariantes explícitos;
- tratamento de erro completo;
- idempotência e reentrância;
- persistência segura;
- compatibilidade de schema;
- testes determinísticos;
- ausência de acoplamento experimental indevido.

## Gate de reprodutibilidade empírica

Antes de aceitar qualquer evidência experimental, revisar:

- hipótese falsificável;
- inputs e task sample congelados;
- executor/provider/model/sandbox identificados;
- versão e configuração registradas;
- budget registrado;
- ambiente e identidade registrados;
- run identity estável;
- execução serial quando exigida;
- raw artifacts preservados;
- verification independente;
- acceptance explícita;
- promoção separada;
- blocked/unknown/not-executed preservados.

## Regras de parada

O trabalho deve parar e registrar `BLOCKED` quando:

- o contrato necessário ainda for implícito;
- uma dependência externa impedir reproducibilidade;
- a identidade do executor/provider/modelo estiver ausente;
- um artifact obrigatório não puder ser preservado;
- uma comparação tiver controles divergentes;
- a única evidência disponível for um teste local;
- a próxima ação exigisse escolher executor sem hipótese ou critério.

## Ordem imediata

1. Finalizar a Fase 0 com baseline executável de ambiente e imports.
2. Completar a Fase 1 com error envelope comum.
3. Implementar os contratos da Fase 2 usando apenas fakes.
4. Só então iniciar lifecycle, persistence e adaptação do baseline.

O plano será atualizado apenas com evidência observada, nunca por inferência de
que uma implementação existente já provou a capacidade correspondente.

## Continuidade registrada — blocos 10 e 11

O bloco 10 introduziu o `ExecutionPlan` como contrato serializável e separado
do resultado da execução. O bloco 11 integrou esse plano à orquestração antes
da invocação do executor. A evidência local atual é de 101 testes focados
passando, com determinismo de serialização, validação de identidade e
compatibilidade entre executor neutro e ponte legada.

Essa evidência não promove executor, provider, modelo, sandbox ou tratamento.
As integrações externas continuam bloqueadas quando faltam suas dependências e
identidades observáveis.

O bloco seguinte adiciona um `CapabilityProfile` e um `CapabilityRegistry`
neutros. A evidência local de 104 testes confirma serialização estável,
ordenação determinística e rejeição de identidades duplicadas. A implementação
não infere capacidades a partir de nomes e não substitui qualification externa.

O bloco seguinte adiciona `ExecutionBudgetSpec` como declaração comum de limites
de execução e identidade por digest. A evidência local de 105 testes cobre
validação e determinismo. A semântica de consumo ainda não foi unificada entre
request, routing, recovery e qualification; essa unificação exige decisão e
testes próprios.

O bloco seguinte integra essa lineage ao `ArtifactStore`: a reserva do próximo
attempt é append-only e grava o vínculo anterior/seguinte atomicamente. A
evidência local de 111 testes cobre persistência, duplicidade e drift de
identidade; execução e verificação continuam fora da operação.

O bloco seguinte integra leitura de lineage ao `AttemptStore`. A evidência local
de 112 testes confirma round-trip e rejeição de drift, preservando artifacts
históricos sem inferir retry a partir apenas do número do attempt.

O bloco seguinte adiciona `RetryPolicy` como autorização determinística e
separada de recovery. A evidência local de 107 testes cobre retryability,
domínio permitido e limites de política/budget. A política não executa retries,
não troca executor e não faz fallback implícito.

O bloco seguinte adiciona lineage determinístico para retries. A evidência local
de 109 testes confirma novo `attempt_id`, preservação do attempt anterior e
ausência de execução automática. A criação de diretório e persistência continuam
separadas para manter reentrância e evitar sobrescrita silenciosa.

O bloco seguinte adiciona `BudgetLedger` imutável, com consumo idempotente por
attempt e rejeição não mutante quando um limite é excedido. A evidência local de
114 testes confirma a propriedade; a integração semântica com os demais budgets
ainda requer decisão própria.

O bloco seguinte liga a especificação de budget ao `ExecutionPlan`, validando o
digest e preservando a identidade durante a orquestração. A evidência local de
115 testes confirma a fronteira; consumo de ledger e enforcement em executor
real continuam separados.

O bloco seguinte persiste o ledger no `RunManifest` com vínculo explícito ao
attempt e ao digest. A evidência local de 116 testes confirma rejeição de drift e
imutabilidade do snapshot; consumo automático pelo executor ainda não é
assumido.

O bloco seguinte persiste atomicamente o manifest validado no artifact store.
A evidência local de 119 testes confirma round-trip e validação prévia de
identidade/lifecycle; verification, acceptance e promotion permanecem estados
separados.

O bloco seguinte integra o ledger ao lifecycle contratual: consumo aceito libera
uma invocação e consumo rejeitado bloqueia antes do executor. A evidência local
de 118 testes confirma a ordem e a ausência de side effect no caminho bloqueado.

O bloco seguinte adiciona `EventLog` persistente sobre o contrato `Event`, com
ordenação temporal e identidade de run verificadas. A evidência local de 121
testes cobre round-trip e fronteiras de erro; o log não substitui manifest,
verification ou promotion.

O bloco seguinte adiciona replay determinístico dos eventos persistidos. A
evidência local de 123 testes cobre identidade e fatos declarados, mantendo
reexecução e acceptance fora do reducer.

O bloco seguinte adiciona validação cruzada entre replay e manifest. A evidência
local de 124 testes confirma detecção de divergência sem escolher uma fonte de
verdade ou reparar estado automaticamente.

O bloco seguinte mantém verification e acceptance como outcomes independentes
no replay. A evidência local de 125 testes confirma comparação com evidências
externas e rejeição de conflito, sem inferência a partir da execução.

O bloco seguinte reconstrói a cadeia completa de referências persistidas. A
evidência local de 127 testes cobre ordem causal e ausência explícita, mantendo
reexecução e decisões fora do reducer.

O bloco seguinte classifica referências explícitas contra um inventário de
artifacts. A evidência local de 129 testes separa presença, ausência e
indeterminação sem dereferenciar URIs ou inventar evidência física.

O bloco seguinte conecta replay ao inventário físico validado do attempt. A
evidência local de 130 testes confirma presença e ausência sem scanning externo,
seleção de substitutos ou promoção implícita.

O bloco seguinte adiciona classificação explícita de integridade da cadeia. A
evidência local de 131 testes distingue completude, ausência e inconsistência
antes de qualquer decisão de acceptance/promotion.

O bloco seguinte materializa a decisão de recovery em plano persistível com
lineage do attempt. A evidência local de 137 testes confirma determinismo e
separação da execução concreta.

O bloco seguinte integra recovery à cadeia de replay como estágio opcional entre
execution e verification. A evidência local de 138 testes confirma causalidade,
compatibilidade e ausência de execução automática.

O bloco seguinte valida a identidade canônica do plano de recovery no replay. A
evidência local de 138 testes confirma rejeição de referências divergentes sem
introduzir execução ou handoff implícito.

O bloco seguinte fecha a identidade entre `ExecutionPlan` e attempt de execução.
A evidência local de 139 testes confirma referências canônicas e rejeição de
drift antes de verification/acceptance.

O bloco seguinte fecha identidade determinística de verification e acceptance,
mantendo namespaces separados. A evidência local de 139 testes confirma
rejeição de drift antes de promotion.

O bloco seguinte fecha a cadeia `verification → acceptance → promotion` com
identidades verificáveis. A evidência local de 139 testes confirma lineage sem
alterar o policy engine ou executar promotion.
