# AGENTS.md

## Contrato operacional mínimo

Leia este arquivo antes de executar qualquer tarefa no repositório.

Se a tarefa entrar em um diretório com outro `AGENTS.md`, leia também o arquivo mais específico; ele complementa ou restringe estas regras.

## 1. Identidade e escopo

- Produto/projeto canônico: **CodePro**.
- `arkx` é namespace Python legado temporário. Não crie novos nomes públicos, worktrees ou documentação atual usando Arkx, exceto ao documentar histórico.
- Não renomeie schemas, fixtures, hashes ou identidades congeladas sem decisão explícita de migração.

## 2. Regras de engenharia

- Prefira a menor arquitetura suficiente para o problema observado.
- Não promova componentes porque já existem.
- Não faça fallback, troca de executor, expansão de escopo ou mudança de tratamento silenciosamente.
- Preserve estados distintos: `BLOCKED != PASS`, `NOT_EXECUTED != PASS`, `EXECUTED != ACCEPTED`, `ACCEPTED != PROMOTED`.
- Uma falha sem evidência de causa permanece não atribuída.

## 3. Quando houver benchmark, paper ou resultado externo

Antes de implementar ou otimizar:

1. identifique repo, commit/versão, config, workload, backend, modelo/provider e verifier usados na referência;
2. reproduza o caminho de referência antes de adaptar;
3. não trate backend apenas suportado como backend comprovado;
4. preserve semântica material: environment, runner, prompt/tools, retry/timeout, patch/submission e verifier;
5. registre qualquer diferença behavior-changing como tratamento/desvio, não como “equivalência”;
6. altere uma variável behavior-changing por vez nos primeiros comparativos;
7. use o verifier oficial como autoridade para claims de benchmark.

Smoke test, fixture sintética, import bem-sucedido ou teste local são evidência local, não resultado de benchmark.

## 4. Reprodutibilidade obrigatória

Para execuções empíricas, registre quando aplicável:

- commit CodePro;
- commit/versão do executor/agente;
- hash/blob da config;
- dataset, subset, split e revision/fingerprint;
- task/instance e base revision;
- imagem + digest/ID resolvido;
- OS/arquitetura;
- modelo/provider e settings efetivos;
- harness/verifier e versão;
- comandos, exit codes e artefatos.

Tag mutável, como `:latest`, nunca é identidade suficiente sozinha.

## 5. Baseline mini-SWE-agent atual

Referência congelada:

- mini-swe-agent `v2.4.6`;
- commit `a83fcae82d2a08f0ee0c688f9d137b3566c097f8`;
- config SWE-bench blob `106decd160e72e5164e29d15d23da354c29c309d`.

No baseline:

- use runner/environment upstream;
- provider-free deve passar antes de modelo/provider;
- routing, recovery, compaction, replanning, handoff e fallback CodePro ficam desligados;
- SWE-ReX, Modal, Harbor e outros substrates são tratamentos/comparadores, salvo evidência de que pertencem à referência histórica;
- SWE-bench oficial é autoridade de `resolved`.

Para repo preparado SWE-bench:

- não exija `HEAD == base_commit`;
- exija `base_commit` ancestral do HEAD preparado;
- exija worktree inicial limpa;
- registre commits de preparação.

Cada prediction/control do verifier usa `run_id` único.

## 6. Antes de commit

Para mudanças de runtime/benchmark:

- rode testes focados do invariável alterado;
- rode `git diff --check`;
- valide JSON alterado;
- mantenha `provider_called = false` em mudanças somente de infraestrutura;
- não reescreva evidência histórica; registre correção/addendum.

## 7. Estado histórico que não pode ser reclassificado

- `Qualification Run v1 = BLOCKED`;
- `promotion = NOT_AUTHORIZED`.

Uma execução posterior não reescreve v1.

## 8. Leitura adicional somente quando necessária

- contrato do projeto: `docs/project-contract.md`;
- política de fidelidade: `docs/benchmark-fidelity-audit.md`;
- baseline mini: `docs/decisions/0142-benchmark-faithful-mini-swebench-substrate.md`;
- estado preparado SWE-bench: `docs/decisions/0143-swebench-prepared-repo-state.md`;
- regras específicas da integração mini: `experiments/integrations/minisweagent/AGENTS.md`.

Não leia toda a árvore de docs por padrão. Abra apenas o material necessário para a tarefa.
