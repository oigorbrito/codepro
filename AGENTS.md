# AGENTS.md

## Contrato operacional do repositório

Leia este arquivo antes de executar qualquer tarefa.

Se o caminho de trabalho contiver outro `AGENTS.md`, leia também o mais específico. A regra mais específica pode restringir este contrato, mas não pode reclassificar evidência histórica nem violar invariantes do projeto.

## 1. Identidade e autoridade

- Produto/projeto canônico: **CodePro**.
- `arkx` é namespace Python legado temporário; não o transforme em nome público novo.
- Não renomeie schemas, fixtures, hashes, proveniência ou identidades congeladas sem migração explícita.
- Ordem de autoridade para uma mudança: contrato/invariante vigente -> código/teste executável -> ADR aplicável -> evidência empírica congelada -> documentação explicativa.
- Evidência histórica é imutável. Correções metodológicas entram como nova decisão/addendum, nunca como reescrita do passado.

## 2. Invariantes

Preserve:

```text
NO_COMPONENT_HAS_TENURE
SCIENTIFIC_SIGNAL != LOCAL_PASS
UPSTREAM_EVIDENCE != LOCAL_EVIDENCE
HYPOTHESIS != IMPLEMENTATION
IMPLEMENTATION != EXECUTED
EXECUTED != ACCEPTED
ACCEPTED != PROMOTED
DONOR != PRODUCT_DEPENDENCY
MECHANISM_PASS != EXECUTOR_ADOPTED
BLOCKED != PASS
NOT_EXECUTED != PASS
NO_SILENT_FALLBACK
NO_SILENT_EXECUTOR_SWITCH
NO_SILENT_SCOPE_EXPANSION
```

Uma falha sem evidência causal permanece não atribuída.

## 3. Roteie a tarefa antes de editar

| Trabalho principal | Leia também | Superfície normativa |
|---|---|---|
| runtime, contratos, arquitetura, CLI | `docs/project-contract.md`, `docs/architecture.md` | `src/AGENTS.md` quando tocar `src/` |
| experimento, benchmark, paper, reprodução | `docs/experimental-protocol.md` e decisão/auditoria da linhagem | `experiments/AGENTS.md` |
| testes, regressão, verificação | contrato/invariante que o teste protege | `tests/AGENTS.md` |
| integração mini/SWE-bench | somente após regras gerais de experimento | `experiments/integrations/minisweagent/AGENTS.md` |

Não leia a árvore inteira de `docs/` por padrão. Abra apenas a fonte normativa/histórica necessária para a tarefa.

## 4. Regra de engenharia

- Faça a menor mudança que satisfaça o contrato observado.
- Nova arquitetura exige necessidade observada, boundary explícito, teste e condição de remoção/rollback.
- Prefira regra executável, schema, teste ou harness quando o requisito puder ser verificado por máquina.
- Prosa não deve duplicar uma regra que já tem fonte normativa mais próxima do trabalho.
- Não “conserte” benchmark, teste ou experimento mudando silenciosamente workload, executor, backend, timeout, retry, prompt, verifier ou critério de aceitação.

## 5. Evidência externa

Quando uma mudança for motivada por benchmark, paper, donor ou implementação upstream:

1. identifique versão/commit/config/workload/backend/modelo/provider/verifier relevantes;
2. separe o que foi observado upstream do que foi reproduzido localmente;
3. reproduza o caminho de referência antes de otimizar ou adaptar;
4. trate diferença behavior-changing como tratamento/desvio explícito;
5. não transforme backend suportado em backend comprovado;
6. não transfira score, qualidade ou validade sem experimento local compatível.

## 6. Validação mínima

Antes de concluir uma mudança:

- execute os testes focados do contrato alterado;
- execute a verificação de repositório aplicável;
- rode `git diff --check`;
- valide formatos estruturados alterados;
- registre limitações, bloqueios e o que não foi executado;
- não declare benchmark/performance sem o verifier e o protocolo correspondentes.

## 7. Pare em vez de improvisar

Pare e reporte `BLOCKED` ou `NOT_EXECUTED` quando:

- uma identidade congelada não puder ser verificada;
- o ambiente exigido não estiver disponível e o único caminho seria fallback;
- uma fonte upstream/material estiver ambígua;
- a mudança exigiria expandir escopo ou autoridade sem aprovação;
- a evidência não sustentar a classificação pretendida.

## 8. Estado histórico preservado

- `Qualification Run v1 = BLOCKED`;
- `promotion = NOT_AUTHORIZED`.

Execuções posteriores não reclassificam essa linhagem.
