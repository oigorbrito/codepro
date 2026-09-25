# AGENTS.md

Aplica-se somente a `experiments/integrations/minisweagent/`.

Leia primeiro o `AGENTS.md` da raiz. Este arquivo contém apenas regras adicionais da integração.

## Referência congelada

- mini-swe-agent `v2.4.6`;
- commit `a83fcae82d2a08f0ee0c688f9d137b3566c097f8`;
- config blob `106decd160e72e5164e29d15d23da354c29c309d`.

Não atualize essas referências silenciosamente.

## Baseline

- Importe/use `get_swebench_docker_image_name()` e `get_sb_environment()` upstream; não replique a lógica no CodePro.
- Não faça fallback para LocalEnvironment, Git Bash, MSYS2, SWE-ReX, Modal ou outro backend.
- Não altere task, dataset revision, prompt, retry, timeout, verifier ou mini para “fazer passar”.
- Não chame modelo/provider antes de provider-free + controles do verifier.
- Mantenha routing, recovery, compaction, replanning, handoff e executor switching desligados.

## Estado da task

Exija:

```text
/testbed
Linux
base_commit ancestral do prepared HEAD
working tree inicial limpa
```

Registre:

- prepared HEAD;
- commits após base_commit;
- dataset revision/fingerprint;
- image name + digest/ID;
- cleanup/lifecycle.

Não exija `HEAD == base_commit`.

## Verifier

- SWE-bench oficial é autoridade para `resolved`.
- Use `run_id` único por negative control, gold control, prediction e agent run.
- Nunca reutilize run_id após mudar o patch.
- P5/local verification do CodePro não substitui o verifier oficial.

## Antes de alterar esta integração

Se uma nova regra for necessária:

1. prove que ela vem da referência upstream ou de evidência empírica;
2. adicione teste de regressão;
3. documente apenas a diferença/invariante nova;
4. não duplique regras já presentes no `AGENTS.md` raiz.
