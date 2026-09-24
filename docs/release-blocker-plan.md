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

### Alvo A — Release do chassi pré-executor

Distribuição instalável, CLI de saúde/baseline e contratos executor-agnostic.
Não promete executar tarefas reais.

### Alvo B — Release operacional privado (alvo atual)

Além do Alvo A, promete submissão de tarefa, execução real, verificação,
persistência de evidência e recuperação. Exige executor qualificado.

O estado atual pode avançar no Alvo A, mas ainda não atende ao Alvo B.

Por decisão de escopo, o Alvo B passou a ser o objetivo: o primeiro release
operacional será privado, sem promessa de publicação aberta. Privado altera a
distribuição e o licenciamento público, mas não reduz os requisitos de
funcionamento, evidência, segurança ou aceitação.

## Matriz de bloqueios

| Ordem | Gate | Evidência atual | Classificação | Próxima ação | Alvo |
|---|---|---|---|---|---|
| 0 | Escopo e identidade | alvo alterado para release operacional privado | `PASS` | definir contrato operacional e executor autorizado | B |
| 1 | Empacotamento | wheel/sdist construídos, instalados em venvs limpos, hashes registrados | `PASS_LOCAL` | aceitar independentemente | A/B |
| 2 | CLI mínimo | `version`, `doctor`, `baseline`; 5 testes focados; `run` rejeitado | `PASS_LOCAL` | confirmação externa no CI | A |
| 3 | Núcleo determinístico | 372 testes e archive limpo passam | `PASS_LOCAL` | executar CI quando Billing estiver resolvido | A/B |
| 4 | Artefatos de publicação | `twine check` e `pip check` passam localmente | `PASS_LOCAL` | repetir externamente e arquivar artefatos | A/B |
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
