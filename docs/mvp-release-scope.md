# Escopo de MVP operacional

## Decisão

O alvo imediato é um MVP operacional. O repositório ainda não deve ser classificado como MVP somente porque a jornada foi implementada; o objetivo é provar uma única jornada operacional vertical, privada e reproduzível.

## Regra contra gambiarra

A única adaptação aceitável é a restrição financeira de infraestrutura: usar
recursos locais, gratuitos ou self-hosted em vez de serviços pagos. Essa
adaptação não pode alterar o contrato, esconder falhas, produzir falso sucesso
ou substituir evidência por opinião. Limitações de hardware, tempo ou custo
devem ser registradas na identidade da execução.

Nenhum atalho técnico, fallback silencioso, fixture apresentada como execução
real ou camada incompleta será promovido como parte do MVP.

## O que o MVP precisa fazer

1. receber uma tarefa real em um repositório autorizado;
2. aplicar uma execução por um único executor explicitamente escolhido;
3. respeitar escopo, orçamento e tempo;
4. executar a verificação declarada;
5. persistir resultado, falha e identidade da execução;
6. retornar estados distintos para sucesso, falha, timeout e ambiente
   indisponível;
7. repetir a mesma tarefa com evidência suficiente para comparar os resultados.

## O que não entra no MVP

- múltiplos executores;
- fallback automático;
- roteamento sofisticado;
- promessa de qualidade geral de modelo;
- SWE-bench como requisito de primeira versão;
- publicação pública;
- compatibilidade com toda a arquitetura histórica.

## Classificação do que já existe

O pacote, `doctor`, `baseline`, testes e checks de artefato são ferramentas de
fundação e harness de desenvolvimento. Eles são necessários para construir o
MVP, mas não constituem por si só uma release operacional.

## Gates do MVP

| Gate | Critério | Estado inicial |
|---|---|---|
| M0 | contrato de uma tarefa, executor, ambiente e aceitação | `VALIDATED` |
| M1 | uma execução real ponta a ponta | `ACCEPTED` |
| M2 | timeout, falha e ambiente indisponível sem falso sucesso | `VALIDATED` |
| M3 | repetição controlada com identidade e evidência | `VALIDATED` |
| M4 | instalação privada e uso por um usuário autorizado | `IMPLEMENTED_NOT_EXECUTED` |
| M5 | aceitação independente e release candidate | `IMPLEMENTED_NOT_EXECUTED` |

Nenhum executor adicional, benchmark amplo ou camada arquitetural nova deve ser
adicionada antes de M1–M3 passarem. A implementação deve preferir remover
complexidade do caminho do MVP a criar novos pontos de extensão.

O contrato detalhado de M0 está em
[0114-mvp-vertical-contract.md](decisions/0114-mvp-vertical-contract.md).

O inventário atual contém um candidato experimental (`p82-baseline-mini-swe-agent`),
mas ele está `FUNCTIONAL_BUT_UNQUALIFIED`: depende de runtime externo e a
superfície de sandbox Git Bash está bloqueada. Ele só pode entrar no MVP depois
de preflight, identidade congelada, execução local reproduzível e aceitação;
não é um executor adotado por existir no código.


## Implementação atual da jornada vertical

A superfície mínima `codepro run` está implementada, mas ainda requer execução
mecânica e evidência antes de qualquer gate ser promovido.

O caminho atual é deliberadamente estreito:

```text
request + authority
-> exact clean Git revision
-> one explicit local-command executor
-> bounded shell-free command
-> changed-file scope check
-> declared verifier
-> append-only evidence
-> explicit terminal result
```

A implementação não seleciona Codex/Claude/Gemini, não chama provider/model e
não faz fallback. Um executor externo pode ser colocado explicitamente no
`argv` somente depois de sua identidade/qualificação ser declarada para o
experimento correspondente.


## M2 + M3 combined validation

The next qualification block is intentionally combined:

```text
M2:
  executor nonzero exit -> FAILED
  command timeout -> TIMED_OUT
  executable unavailable -> ENVIRONMENT_UNAVAILABLE
  none may reach VERIFIED

M3:
  repeat frozen Issue #57 twice
  same repository/base/task/executor/verifier
  explicit distinct attempt_id
  distinct run_id/evidence
  identical authorized changed-file set
  identical workspace.patch sha256
  both VERIFIED
```

Runner: `tools/run_m2_m3_validation.py`.

Implementation is not execution evidence. M2/M3 remain
`IMPLEMENTED_NOT_EXECUTED` until the runner is executed successfully.


## M2 + M3 observed result

Observed local evidence on Python 3.13:

```text
classification = M2_M3_VALIDATED

M2:
  FAILED
  TIMED_OUT
  ENVIRONMENT_UNAVAILABLE

M3:
  both_verified = true
  distinct_attempt_id = true
  distinct_run_id = true
  same_base_sha = true
  same_changed_files = true
  same_patch_sha256 = true
  same_task_id = true
```

This closes M2 and M3 at local validation scope only. It does not authorize
executor promotion or release.


## M4 + M5 readiness block

Runner: `tools/run_m4_m5_readiness.py`.

The combined block validates:

```text
M4:
  exact candidate SHA
  clean Python virtual environment
  non-editable private package install
  installed codepro console script
  public CLI probes
  one authorized VERIFIED vertical through installed CLI

M5 readiness:
  M1 acceptance evidence present and ACCEPTED
  M2/M3 evidence present and VALIDATED
  exact candidate clean checkout
  foundation check
  baseline
  full unittest suite
  mutation probe
  chassis fingerprint
  compileall
```

A successful result is readiness for independent release-candidate review, not
a release authorization. Tagging, publication, executor promotion, and
activation remain separate explicit decisions.
