# Requisitos do MVP derivados de benchmarks

## Evidência externa usada

- [SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/)
  fornece um repositório/revisão, um issue e verificadores separados para
  testes `FAIL_TO_PASS` e `PASS_TO_PASS`.
- [Terminal-Bench](https://www.tbench.ai/news/announcement) usa tarefas com
  ambiente dedicado, solução verificada por humanos e scripts de teste; a
  versão atual também explicita recursos e versões do benchmark.

Esses benchmarks medem resolução de tarefas por agentes. Não qualificam o
chassi isoladamente nem autorizam adotar um executor.

## Tradução para o chassi

| Observação do benchmark | Requisito do MVP | Estado |
|---|---|---|
| revisão/base precisa ser identificável | request exige `environment.revision` | implementado |
| tarefa precisa de workspace definido | governance exige `environment.workspace` | implementado |
| solução precisa de verificação declarada | `acceptance_checks` e autoridade devem permanecer explícitos | contrato existente |
| verificador precisa ser reproduzível | `TestResult` preserva `command`, `exit_code` e `duration_ms` quando observados | implementado |
| tarefa precisa de um teste executável no ambiente | `run_verification_command` executa argv declarado, sem shell, com timeout e stdout/stderr | implementado |
| resultado precisa separar correção de execução | verification/acceptance continuam estados distintos | contrato existente |
| ambiente e recursos afetam o resultado | environment, configuração e budget precisam ser persistidos | parcial |
| falhas de infraestrutura não são rejeições da tarefa | erro de ambiente permanece `BLOCKED`/explícito | contrato existente |
| comparação precisa de controles compatíveis | identidade de task, revisão, executor, ambiente e budget | contrato existente |

## Limite da conclusão

Os requisitos acima tornam a execução mensurável e reproduzível. Não provam que
um executor resolve tarefas. Essa prova só começa no M1, com um executor real,
um task set congelado e verificadores executados de verdade.
