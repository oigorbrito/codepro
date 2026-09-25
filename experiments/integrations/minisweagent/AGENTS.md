# AGENTS.md

Aplica-se somente a `experiments/integrations/minisweagent/`.

Leia primeiro `/AGENTS.md` e `/experiments/AGENTS.md`. Este arquivo contém apenas regras específicas da referência mini/SWE-bench.

## Referência congelada

- mini-swe-agent `v2.4.6`;
- commit `a83fcae82d2a08f0ee0c688f9d137b3566c097f8`;
- config SWE-bench blob `106decd160e72e5164e29d15d23da354c29c309d`.

Não atualize essas referências silenciosamente.

## Baseline

- Use/import upstream `get_swebench_docker_image_name()` e `get_sb_environment()`; não replique essa lógica no CodePro.
- O baseline é Docker/Linux, `/testbed`, com a configuração upstream pinada.
- Não faça fallback para LocalEnvironment, Git Bash, MSYS2, SWE-ReX, Modal, Harbor ou outro substrate.
- Não altere task, prompt, retry, timeout, verifier ou mini para obter PASS.
- Não chame modelo/provider antes de provider-free + controles do verifier.
- Routing, recovery, compaction, replanning, handoff e executor switching CodePro ficam desligados.

## Estado preparado da task

Exija:

```text
base_commit ancestral do prepared HEAD
AND working tree inicial limpa
```

Registre prepared HEAD e commits de preparação. Não exija `HEAD == base_commit`.

## Verifier

- O SWE-bench oficial é a autoridade para `resolved`.
- Use `run_id` distinto para negative control, gold control e cada prediction/agent run.
- Nunca reutilize `run_id` depois de alterar prediction diff.
- P5/local verification do CodePro não substitui o verifier oficial.

## Antes de alterar a integração

Uma nova regra precisa de referência upstream ou evidência empírica, teste de regressão e registro da diferença/invariante. Não duplique regras já herdadas dos `AGENTS.md` superiores.
