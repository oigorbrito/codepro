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
| M0 | contrato de uma tarefa, executor, ambiente e aceitação | `IMPLEMENTED_NOT_EXECUTED` |
| M1 | uma execução real ponta a ponta | `NOT_EXECUTED` |
| M2 | timeout, falha e ambiente indisponível sem falso sucesso | `PENDING` |
| M3 | repetição controlada com identidade e evidência | `PENDING` |
| M4 | instalação privada e uso por um usuário autorizado | `PENDING` |
| M5 | aceitação independente e release candidate | `PENDING` |

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
