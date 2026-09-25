# AGENTS.md

Aplica-se a `src/`.

## Engenharia e arquitetura

- Implemente somente comportamento autorizado por contrato, ADR ou necessidade observada.
- Preserve boundaries de autoridade: observação não decide sucesso; verification não decide acceptance; acceptance não decide promotion.
- Não introduza orchestration, executor selection, fallback, network/provider calls ou product integration em um boundary que hoje é determinístico sem uma decisão explícita.
- Dependência nova exige benefício observável, impacto de portabilidade/teste documentado e alternativa mais simples considerada.
- Prefira funções/contratos pequenos, determinísticos e removíveis.
- Compatibilidade com o namespace legado `arkx` não autoriza novos nomes públicos Arkx.

## Para qualquer mudança em código

1. identifique o contrato/invariante alterado;
2. escreva ou atualize teste que falhe sem a mudança;
3. implemente a menor correção;
4. execute testes focados e os checks de fundação aplicáveis;
5. não use uma refatoração ampla para esconder mudança semântica.

## Mudanças de arquitetura

Uma nova camada, controller, registry, adapter ou abstraction só entra se houver:

- responsabilidade distinta;
- input/output claros;
- authority boundary;
- falha que a abstração evita;
- teste que prova o boundary;
- condição de remoção ou substituição.

Se esses itens não existirem, não crie a abstração.
