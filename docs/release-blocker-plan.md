# Plano passo a passo de desbloqueio de release

## Regra de decisão

Cada bloqueio recebe uma classificação explícita:

- `PASS`: evidência executada atende ao critério declarado;
- `PENDING`: ainda falta trabalho ou decisão, mas não há falha conhecida;
- `BLOCKED_INFRA`: o teste não iniciou por infraestrutura externa;
- `NOT_APPLICABLE`: não pertence ao alvo de release atual, com justificativa;
- `NO-GO`: falha funcional ou evidência insuficiente para promoção.

`NOT_APPLICABLE` não pode ser usado para esconder uma capacidade anunciada.
Uma pendência só pode ser ignorada quando o escopo do release não promete a
capacidade correspondente.

## Alvos distintos

### Fundação obrigatória — Chassi pré-executor

O chassi não é um produto alternativo nem um release final. É a fundação
obrigatória do produto operacional: distribuição instalável, contratos,
governança, telemetria, persistência, recuperação, verificação e fronteiras
executor-agnostic. Ele precisa estar validado antes de receber um executor.

Uma versão do chassi pode ser usada internamente como artefato técnico, mas não
será apresentada como o release do CodePro.

### Alvo B — Release operacional privado (alvo atual)

Além do Alvo A, promete submissão de tarefa, execução real, verificação,
persistência de evidência e recuperação. Exige executor qualificado.

O estado atual pode avançar no Alvo A, mas ainda não atende ao Alvo B.

Por decisão de escopo, o Alvo B é o objetivo: o primeiro release operacional
será privado, sem promessa de publicação aberta. O chassi é um gate obrigatório
desse alvo. Privado altera a distribuição e o licenciamento público, mas não
reduz os requisitos de funcionamento, evidência, segurança ou aceitação.

## Matriz de bloqueios

| Ordem | Gate | Evidência atual | Classificação | Próxima ação | Alvo |
|---|---|---|---|---|---|
| 0 | Escopo e identidade | alvo alterado para release operacional privado | `PASS` | definir contrato operacional e executor autorizado | B |
| 1 | Empacotamento do chassi | wheel/sdist construídos, instalados em venvs limpos, hashes registrados | `PASS_LOCAL` | aceitar independentemente | B |
| 2 | CLI mínimo do chassi | `version`, `doctor`, `baseline`; 5 testes focados; `run` rejeitado | `PASS_LOCAL` | confirmação externa no CI | B |
| 3 | Núcleo determinístico do chassi | 372 testes e archive limpo passam | `PASS_LOCAL` | executar CI quando Billing estiver resolvido | B |
| 4 | Artefatos de publicação do chassi | `twine check` e `pip check` passam localmente | `PASS_LOCAL` | repetir externamente e arquivar artefatos | B |
| 5 | CI externo | jobs criados, mas nenhum passo iniciou por falha de Billing/spending limit | `BLOCKED_INFRA` | corrigir Billing ou configurar runner próprio | A/B |
| 6 | Política privada e notas de release | não há política de distribuição privada nem `CHANGELOG`/release notes identificados | `PENDING_HUMAN_DECISION` | definir acesso, retenção de evidências e notas da versão | B |
| 7 | Aceitação independente | ainda não existe decisão `ACCEPT` para a revisão candidata | `PENDING` | autoridade independente revisar evidências | A/B |
| 8 | Executor/CLI externo | execução real é requisito do novo alvo | `NO-GO` | escolher um executor autorizado e qualificá-lo | B |
| 9 | Benchmark operacional | SWE-bench/provider benchmark requer executor e tarefa real | `PENDING` | executar após o fluxo operacional local passar | B |
| 10 | Promoção | branch de auditoria diverge de `main`; sem tag/release candidate | `PENDING` | congelar revisão, revisar diff, aceitar e só então taggear | A/B |

## Sequência sem atalhos

1. Definir o contrato do release operacional privado: entrada, tarefa, saída,
   limites, evidências e política de falha.
2. Escolher explicitamente o executor autorizado e sua superfície de integração.
3. Implementar o fluxo operacional real sobre o chassi atual.
4. Executar primeiro toda a validação local: build, `twine check`, instalação,
   CLI, `pip check`, suíte, testes negativos e execução real controlada.
5. Corrigir Billing/spending limit ou registrar runner próprio seguro.
6. Reexecutar o workflow externo completo: build, instalação, CLI,
   `pip check` e suíte.
7. Arquivar logs, hashes, identidade do ambiente e resultado bruto do CI.
8. Obter decisão independente `ACCEPT` ou manter `NO-GO`.
9. Executar benchmark externo compatível, sem alegar mais do que o teste mede.
10. Criar uma revisão candidata sem artefatos locais; revisar diff contra a
   base escolhida.
11. Gerar release candidate e repetir instalação em ambiente limpo.
12. Publicar a release privada somente se todos os gates obrigatórios estiverem
    `PASS`.

## Decisões que não serão mascaradas

- Billing não vira `PASS` por testes locais; permanece `BLOCKED_INFRA`.
- CLI externo não vira `PASS` por existir documentação; permanece pendente.
- benchmark não é executado artificialmente sem executor e tarefa compatíveis.
- ausência de licença/notas exige decisão; não será corrigida por suposição.
- a branch de auditoria não será mesclada em `main` por conveniência.
