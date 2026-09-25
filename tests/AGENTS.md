# AGENTS.md

Aplica-se a `tests/`.

## Papel da suíte

Testes são a fronteira executável dos contratos do CodePro. Eles provam comportamento local sob as condições testadas; não provam benchmark, validade externa ou promoção.

## Ao criar ou alterar testes

- Nomeie o invariante/comportamento protegido.
- Inclua caso negativo para regras fail-closed ou authority boundaries.
- Para correção de bug, mantenha um teste de regressão que falhe no comportamento anterior.
- Não faça mock do próprio boundary que o teste pretende qualificar.
- Evite asserts que apenas repetem implementação interna sem verificar comportamento observável.
- Preserve `BLOCKED`, `NOT_EXECUTED` e estados intermediários; não colapse tudo em booleano de sucesso.
- Quando houver cache, run ID, retry, timeout ou fallback, teste também a condição que poderia mascarar um falso positivo.

## Benchmark/verifier

- Teste unitário do CodePro não substitui verifier oficial.
- Gold/negative controls pertencem ao harness experimental correspondente, não devem ser simulados aqui como prova de benchmark.
