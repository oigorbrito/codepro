# CodePro — Benchmark Fidelity Audit v2

Data da auditoria: 2026-09-24

Conclusão: `REFERENCE_BASELINE_PARTIALLY_FAITHFUL`

Promotion: `PROMOTION_NOT_AUTHORIZED`

Qualification Run v1: `BLOCKED`

## Escopo e autoridade

Esta auditoria compara o caminho de referência do `mini-swe-agent` com o que o
CodePro declara ou executa. Presença de código, suporte de backend, teste local
ou preflight não é tratado como prova de resultado de benchmark.

Referência principal:

- repositório: `SWE-agent/mini-swe-agent`;
- commit: `a83fcae82d2a08f0ee0c688f9d137b3566c097f8`;
- versão: `2.4.6`;
- configuração: `src/minisweagent/config/benchmarks/swebench.yaml`;
- Git blob da configuração: `106decd160e72e5164e29d15d23da354c29c309d`.

Topologia de referência observada:

`swebench runner → get_sb_environment() → DockerEnvironment → Linux task image → /testbed → bash -c → BASH_ENV → agent loop → submission → official evaluator`.

O CodePro qv2 confirmou identidade, configuração, Docker Linux e probe de
container, mas ainda não executou uma task SWE-bench completa com provider,
patch e verifier oficial.

## Evidência local

- CodePro qv2: `eb8ec36337c0b936d869c2bf49d2e062a5935e4a`.
- Mini qv2: `a83fcae82d2a08f0ee0c688f9d137b3566c097f8`.
- Preflight provider-free: `BENCHMARK_SUBSTRATE_READY`.
- Probe Linux `python:3.11`: 3/3 pass, sem containers residuais.
- Probe direto do `DockerEnvironment`: 1 execução completa; 2 execuções
  instáveis no Windows; cleanup upstream deixou residual em 2 execuções.
- Evidência do probe: `.tmp/mini-docker-environment-summary.json`.
- Não há evidência local de patch verificável nem de verifier oficial executado.

## Matriz de fidelidade

| Subsystem | External evidence | Exact reference | CodePro implementation | Difference | Material? | Classification | Baseline allowed? |
|---|---|---|---|---|---|---|---|
| environment | Referência usa DockerEnvironment Linux | mini commit; `environments/docker.py` | abstrações `src/arkx/environment.py`; qv2 somente preflight | CodePro original não é o runner upstream; host histórico usa Windows/Git Bash | yes | `SUBSTRATE_MISMATCH` | no |
| runner | Runner upstream possui `get_sb_environment`, dataset mapping e preds | `run/benchmarks/swebench.py` | não há runner CodePro provado como behavior-neutral | caminho completo ainda não executado pelo CodePro | yes | `AUDIT_REQUIRED` | no |
| agent | `DefaultAgent` upstream e trajetória mini | `agents/default.py` | CodePro possui orchestration própria | sem prova de equivalência semântica | yes | `SEMANTIC_MISMATCH` | no |
| prompt | Prompt bundled no YAML pinado | `config/benchmarks/swebench.yaml` | não há execução CodePro com prompt efetivo provado | prompt/configuração efetiva futura ainda não congelada | yes | `CONFIG_DRIFT` | no |
| tools | Bash tool/action parser upstream | `models/litellm_model.py`; action utilities | CodePro possui contratos próprios de execução | não demonstrada preservação do tool contract | yes | `AUDIT_REQUIRED` | no |
| model adapter | LiteLLM e provider ficam no mini config | `models/litellm_model.py` | CodePro tem abstrações/adapters próprios | OpenRouter/provider histórico não é prova do modelo bundled | yes | `SEMANTIC_MISMATCH` | no |
| provider | Resultado externo exige provider/model exatos | protocolo P8.2 local | OpenRouter aparece em experimentos CodePro | provider/configuração diferem da referência bundled | yes | `CONFIG_DRIFT` | no |
| retry | Mini usa tenacity, até 10 tentativas por padrão | `models/utils/retry.py` | CodePro possui política de retry separada | não há prova de mesma contagem/backoff/custo | yes | `SEMANTIC_MISMATCH` | no |
| timeout | Mini environment: 60s no YAML; pull separado | YAML pinado; `docker.py` | histórico CodePro usou watchdog 190s | 190s não é limite da referência | yes | `CONFIG_DRIFT` | no |
| context | Mini formata observação upstream | `models/litellm_model.py`; YAML | CodePro implementou treatments de compaction/truncation | treatments não pertencem ao baseline reference | yes | `CODEPRO_ORIGINAL` | no |
| compaction | Não há compaction CodePro na referência upstream | YAML/model upstream | blocos A/B de compaction existem em evidência local | sintético/experimental; Wave 0 bloqueada | yes | `SYNTHETIC_ONLY` | no |
| routing | Não faz parte do runner upstream | n/a | `src/arkx/routing.py` | política própria, sem benchmark pareado | yes | `CODEPRO_ORIGINAL` | no |
| planning | Não faz parte da cadeia mínima upstream | n/a | `src/arkx/planning.py` | mecanismo CodePro adicional | yes | `CODEPRO_ORIGINAL` | no |
| recovery | Não faz parte do agent loop upstream de referência | n/a | `src/arkx/recovery.py` | replan/escalate/handoff próprios | yes | `CODEPRO_ORIGINAL` | no |
| handoff | Nenhuma evidência externa vinculada ao benchmark | n/a | `src/arkx/handoff.py` | multi-executor não qualificado | yes | `CODEPRO_ORIGINAL` | no |
| patch extraction | Upstream produz `submission`/`model_patch` em `preds.json` | `swebench.py` | CodePro tem boundaries de patch próprias | não provado que usa submission upstream diretamente | yes | `AUDIT_REQUIRED` | no |
| verifier | Autoridade oficial é `swebench.harness.run_evaluation` | protocolo P8.2 | P5 CodePro é separado | P5 não pode gerar resolved oficial | yes | `SEMANTIC_MISMATCH` | no |
| dataset | Upstream distingue full/verified/lite/etc. | `DATASET_MAPPING` | CodePro registra amostras locais | subset/revision não pode ser generalizado | yes | `AUDIT_REQUIRED` | no |
| instrumentation | Upstream salva trajetória; CodePro adiciona telemetria | `Agent.save`; logs CodePro | timing/process tracing pode alterar execução | neutralidade ainda não provada | yes | `AUDIT_REQUIRED` | no |
| governance | Não é parte do benchmark agent loop | n/a | contracts de evidência/acceptance/promotion | pode envolver baseline somente se passivo | no | `REFERENCE_DERIVED` | yes, passivo |
| acceptance | Resultado oficial separado de execução | SWE-bench harness | CodePro tem acceptance/promotion próprios | não substitui autoridade oficial | yes | `SEMANTIC_MISMATCH` | no |
| promotion | Benchmark não autoriza promoção do produto | n/a | CodePro mantém promotion explícita | estado correto, sem evidência de promoção | no | `PROMOTION_NOT_AUTHORIZED` | no |

## Classificações de evidência

| Item | Estado |
|---|---|
| Identidade do mini/configuração | `REFERENCE_MIRROR` |
| Docker/Linux preflight | `REFERENCE_DERIVED` / `SUPPORTED_BACKEND_ONLY` |
| DockerEnvironment real 3/3 | `AUDIT_REQUIRED` |
| Task SWE-bench real com patch/verifier | `EVIDENCE_NOT_FOUND` |
| Routing, recovery, handoff e compaction | `SYNTHETIC_ONLY` / `CODEPRO_ORIGINAL` |
| Qualquer score transferido para CodePro | `PROMOTION_NOT_AUTHORIZED` |

## Decisão

O CodePro preserva a identidade e parte do substrate de referência em qv2,
mas ainda não preserva demonstradamente todas as condições materiais do
benchmark. A diferença Windows/Git Bash versus Docker/Linux, o caminho de
runner não executado, o provider/modelo não qualificado, os tratamentos próprios
e a ausência de patch/verifier impedem chamar o baseline de fiel.

O próximo experimento deve ser provider-free e usar a imagem SWE-bench exata:
`get_swebench_docker_image_name(sympy__sympy-14711)` → `get_sb_environment()` →
`/testbed` → Git/base state → comandos Bash → controle do verifier. Só depois
de esse caminho passar deve haver execução com modelo/provider. Nenhum routing,
recovery, handoff ou compaction entra nessa linha.

Conclusão permitida: `REFERENCE_BASELINE_PARTIALLY_FAITHFUL`.
