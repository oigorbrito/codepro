# AGENTS.md

Aplica-se a `experiments/`.

## Engenharia experimental

Experimento é produção de evidência, não demonstração de que a hipótese “funciona”.

Antes de executar, congele quando aplicável:

- pergunta/hipótese;
- workload e amostragem;
- tratamento e comparator;
- métricas;
- repetitions/stopping rule;
- analysis plan;
- environment;
- critério de aceitação/promoção.

## Proveniência mínima

Registre identidades imutáveis ou fingerprints resolvidos para:

- CodePro;
- executor/agente;
- config;
- dataset/subset/split/revision;
- task/instance/base revision;
- image digest/ID e OS/arch;
- model/provider/settings;
- harness/verifier;
- comandos, timestamps, exit codes e artefatos.

Tag mutável sozinha não é identidade suficiente.

## Comparação

- O baseline de referência deve preservar o caminho upstream antes de qualquer tratamento CodePro.
- Mude uma variável behavior-changing por vez nos primeiros comparativos.
- Use mesmo workload e mesmo verifier; mantenha model/provider fixos salvo quando forem a variável tratada.
- Meça, quando material: resolved/quality, tokens, cost, wall time, provider calls, retries, timeouts e failure classes.
- Instrumentação nova precisa de teste de neutralidade quando puder alterar timing, contexto, subprocessos ou I/O.

## Controles

Quando o harness permitir:

- negative/no-op control deve falhar;
- positive/gold control deve resolver;
- prediction/agent run é uma terceira classe, nunca substitui os controles;
- IDs de execução/cache devem ser únicos quando o harness os usa como chave.

## Interpretação

Separe explicitamente:

```text
OBSERVADO
INFERIDO
NÃO_TESTADO
BLOQUEADO
```

Smoke, fixture sintética, import, startup ou teste local não são resultado de benchmark.

Falha, timeout e bloqueio permanecem nos dados. Não substitua por fallback e não descarte run inconveniente sem regra prévia.
