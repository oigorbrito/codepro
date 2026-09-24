# Codepro — plano de prontidão para release

Identidade do produto: **Codepro**. O namespace técnico atual é `arkx`, por
compatibilidade; isso não altera a identidade da distribuição nem do release.

Status inicial: **NO-GO** para release de produto operacional.

Este documento define a sequência de avaliação do produto. Um gate só pode ser
marcado como `PASS` com evidência executada e arquivada. `PASS` de teste local
não será chamado de benchmark externo, qualificação de executor ou evidência
de usuário.

Para a matriz operacional de bloqueios e a distinção entre release do chassi e
release operacional, consulte [o plano passo a passo](release-blocker-plan.md).

## Objetivo do release

O release de produto só será promovido quando um usuário conseguir, em um
ambiente limpo e suportado:

1. instalar o artefato;
2. iniciar o CLI;
3. submeter uma tarefa;
4. obter planejamento/roteamento explícito;
5. executar o caminho suportado;
6. receber resultado verificável ou falha explícita;
7. reproduzir a execução usando os artefatos registrados.

O `v0.2.0` existente não recebe retroativamente essa classificação: a evidência
atual o sustenta apenas como release técnico/chassi.

## Base metodológica

- **PyPA Packaging Flow**: a publicação deve partir de uma árvore versionada,
  declarar metadados, gerar sdist/wheel e verificar a instalação pelo usuário.
  Referências: [flow](https://packaging.python.org/en/latest/flow/) e
  [building and publishing](https://packaging.python.org/en/latest/guides/section-build-and-publish/).
- **NIST SSDF 1.1**: fornece práticas de desenvolvimento seguro, rastreabilidade
  e redução de risco; não é prova de funcionalidade do agente. Referência:
  [NIST SP 800-218](https://doi.org/10.6028/NIST.SP.800-218).
- **SWE-bench**: exige dataset, identidade da execução, timeout, artefatos e
  relatório; um caso resolvido não representa qualidade geral. Referências:
  [evaluation CLI](https://github.com/SWE-bench/SWE-bench/blob/main/docs/reference/cli.md)
  e [evaluation guide](https://github.com/SWE-bench/SWE-bench/blob/main/docs/guides/evaluation.md).
- **Engenharia empírica**: cada afirmação deve ter hipótese falsificável,
  workload congelado, tratamento identificado, métrica, repetição, falhas
  reportadas e artefatos brutos. Não serão aceitos cherry-picking, fallback
  silencioso ou inferência de sucesso por ausência de erro.

## Gates, em ordem

### G0 — Identidade e reprodutibilidade

Hipótese: a revisão avaliada é a mesma que será publicada e pode ser
reconstruída sem depender do estado acidental da máquina.

Critérios:

- branch/tag/commit, versão, Python, SO e dependências registrados;
- working tree limpo ou desvios explicitamente anexados;
- branch local reconciliada com a revisão de release;
- comando de avaliação documentado e repetível.

Evidência atual: **FAIL/INDETERMINADO**. A branch local está 24 commits atrás
e 22 à frente de `origin/main`, com artefatos locais não rastreados.

### G1 — Distribuição e instalação limpa

Hipótese: um usuário consegue instalar e iniciar o produto sem `PYTHONPATH`,
checkout especial ou dependência implícita.

Critérios:

- `pyproject.toml` com metadados e versão;
- sdist e wheel construídos;
- instalação em venv novo;
- `codepro --version`, `doctor` e `inspect` executam;
- arquivos fora do artefato não são necessários.

Evidência atual: **FAIL na branch auditada**. O comando comum falha ao importar
`arkx`; os testes passam somente com `PYTHONPATH=src`.

### G2 — Núcleo determinístico

Hipótese: contratos, estados, persistência, replay e falhas determinísticas
mantêm o comportamento declarado.

Critérios:

- suíte completa em ambiente suportado;
- testes de unidade, integração e fronteiras negativas;
- mutation probe sem mutação sobrevivente nas invariantes críticas;
- nenhum teste depende de ordem, diretório ou lixo de execução anterior.

### G3 — Caminho mínimo de produto sem provedor

Hipótese: o produto coordena uma tarefa completa com executor falso, sem
acoplar o contrato central a um fornecedor.

Critérios:

- entrada → caracterização → roteamento → plano → execução → verificação →
  aceitação/promoção;
- sucesso, timeout, cancelamento, orçamento excedido e dependência ausente;
- eventos e artefatos persistidos atomicamente;
- replay independente reproduz o estado final.

### G4 — Segurança e operação básica

Hipótese: o caminho mínimo falha de modo seguro e observável.

Critérios:

- escopo autorizado e comandos perigosos bloqueados;
- segredos não aparecem em logs;
- dependências auditadas;
- artefatos possuem hash e identidade;
- documentação informa limites e recuperação.

### G5 — Qualificação de um executor real (adiado)

Este gate não faz parte do objetivo atual. Ele só será aberto depois que G0–G4
estiverem aprovados e quando houver uma decisão explícita de integrar um
executor. O fake de G3 existe apenas para provar o contrato do produto.

Hipótese futura: um executor específico, com versão/configuração fixas,
completa o fluxo real sob um contrato definido.

Critérios:

- identidade do executor, provedor, modelo e versão;
- preflight positivo, sem tratar PATH como disponibilidade;
- tarefa pequena reproduzível em ambiente limpo;
- edição real, testes reais e resultado verificável;
- falhas de autenticação, timeout, processo e dependência registradas;
- repetição serial com o mesmo tratamento e artefatos brutos.

Dois ou três executores só são necessários se o produto fizer essa promessa.
Não serão usados como fallback implícito.

### G6 — Capacidade por horizonte de tarefa

Hipótese: o produto sustenta as classes que declara vender.

Critérios separados para pequena, média e longa duração: workload congelado,
limite de tempo, orçamento, taxa de conclusão, taxa de regressão, falha de
infraestrutura e custo. Uma vitória em SWE-bench Gold não qualifica todas as
classes nem um provedor/modelo em geral.

### G7 — Release candidate e promoção

Hipótese: outra pessoa consegue reconstruir, instalar, operar e auditar o
release a partir dos artefatos publicados.

Critérios:

- CI verde na revisão exata;
- artefatos, hashes, SBOM/auditoria e logs publicados;
- relatório com configuração, runs brutos, limitações e falhas;
- README reproduz o caminho suportado;
- decisão independente `ACCEPT` antes de tag/publicação.

## Ordem de execução adotada

1. congelar a revisão de produto e separar a linha de auditoria da linha de
   release;
2. corrigir G0 e G1 antes de qualquer executor;
3. executar G2 com ambiente limpo;
4. executar G3 e G4, incluindo testes negativos;
5. escolher explicitamente um executor para G5;
6. executar G6 apenas para as classes anunciadas;
7. preparar G7; qualquer falha mantém `NO-GO`.

## Auditoria inicial do plano

O plano foi auditado contra as fontes acima e contra a árvore local.

| Propriedade | Resultado |
|---|---|
| Começa pelo uso do usuário e instalação | PASS |
| Separa teste local de benchmark externo | PASS |
| Exige identidade, configuração e artefatos | PASS |
| Trata falha e infraestrutura como estados explícitos | PASS |
| Evita exigir múltiplos executores sem promessa correspondente | PASS |
| Possui critérios falsificáveis por gate | PASS |
| Estado atual do produto | NO-GO |

### Evidência da primeira rodada

- `git diff --check`: `PASS`.
- `python tools/check_foundation.py`: `PASS` — 8 arquivos e 14 invariantes.
- `PYTHONPATH=src python -m unittest discover -s tests -t .`: `PASS` — 367
  testes.
- `python -m unittest discover -s tests -t .`: `FAIL` — o pacote não é
  importável sem configuração adicional.
- `python tools/mutation_probe.py`: `NOT MEASURED` nesta branch; o script não
  existe nela. A ausência do probe não será convertida em aprovação.
- working tree: `BLOCKED_FOR_RELEASE` por artefatos locais preexistentes e pela
  divergência entre a branch auditada e `origin/main`.
- auditoria de `origin/main` em `bb1b4547`: o `pyproject.toml` declara
  `requires-python >=3.12`, mas a instalação limpa com Python 3.13 ficou
  `BLOCKED_INFRA` porque o ambiente não conseguiu inicializar `venv`, acessar
  `setuptools` ou criar/limpar diretórios temporários. Isso não é aprovação nem
  reprovação funcional; exige repetição em um ambiente limpo com permissões
  válidas.
- repetição de G1 em `origin/main@bb1b4547`, Python 3.13.15: wheel e sdist
  construídos; wheel instalado em venv separado; `codepro --version`, `doctor`
  e `inspect --json`: `PASS`.
- hashes dos artefatos dessa rodada: wheel
  `D9890489615E032B0A071F6E3E9D196FBEC4ADE44997DED6EB25D51AB855CFFF`;
  sdist `61AC55CA74CA3F11BF221EC8287E028DCCE34B478BAD30370EE92D009B51C665`.
- G2 na mesma instalação: `344` testes, `1` skip, `PASS` com permissões
  adequadas. Sem elevação houve `12` erros de ACL em `tempfile`; esse resultado
  permanece como limitação do ambiente, não como aprovação silenciosa.
- G3: contratos internos de governança, roteamento, qualificação e recovery
  passaram em `63` testes, mas o CLI público só expõe `doctor` e `inspect`.
  `codepro run` é rejeitado pelo parser (`invalid choice`). Não existe ainda
  caminho público para submeter tarefa, acionar executor, verificar resultado
  ou persistir uma execução de usuário. G3 permanece
  `BLOCKED_BY_PRODUCT_SCOPE`.
- implementação de G3 foi preparada isoladamente na branch
  `codex/g3-cli-execution`, commit `ef1cf6cb`: `codepro run --executor fake`
  cobre sucesso, timeout e erro de ambiente; persiste JSON atomicamente; 348
  testes passaram com 1 skip. O wheel dessa implementação teve SHA-256
  `3F837651F00B40BDDB71A546985A2032B8CF53ECBD12175058EF0C589E67C2D6`.
  Isso é evidência de contrato público com fixture, não qualificação de
  executor real e ainda não é promoção para `main`.
- escopo atual confirmado: G5 está `DEFERRED`; nenhum executor real será
  procurado, selecionado ou promovido durante a preparação do chassi.
- decisão de escopo: integração com CLI externo permanece `PENDING`, fora do
  acceptance atual do chassi. Isso não bloqueia a avaliação do pacote, do CLI
  mínimo e dos contratos executor-agnostic; bloqueia qualquer release que se
  anuncie como produto operacional capaz de executar tarefas reais.
- G4 na implementação G3 (`ef1cf6cb`): `110` testes focados, `1` skip,
  `PASS`, cobrindo comando sem shell, governança, autorização, qualificação,
  escopo, CLI, verificação, promoção e proveniência. O foundation check também
  passou com `10` arquivos, `14` invariantes e `2` study guards.
- validação do artefato empacotado na implementação G3 (`ef1cf6cb`): wheel
  construído e instalado em venv Python 3.13 sem `PYTHONPATH`; `codepro
  0.2.0`, `doctor` e `inspect --json`: `PASS`. SHA-256 do wheel:
  `3578CD89FD09716ABC9A4093D83AB5050AC795924A73E1749D46141D070ACD34`.
- contrato público G3 no wheel instalado: os três estados foram reproduzidos e
  persistidos atomicamente (`READY_FOR_ACCEPTANCE`, `COMMAND_TIMEOUT` e
  `ENVIRONMENT_ERROR`), com JSONs brutos separados por tentativa.
- regressão do artefato instalado: `348` testes, `1` skip, `PASS`.
- probe empírico de mutações na implementação G3: `8/8` mutações mortas,
  `0` sobreviventes (`MUTATION_PROBE_PASS`). Isso aumenta a confiança nas
  invariantes, mas não substitui teste de usuário, integração externa ou
  qualificação de executor.
- reconciliação G3 com a linha de auditoria (`acd90a27`): `BLOCKED`. O
  cherry-pick de `ef1cf6cb` encontrou conflitos modify/delete em
  `src/arkx/cli.py` e `tests/test_cli.py`; a linha de auditoria não contém
  esses arquivos nem os módulos antigos importados pelo CLI (`command`,
  `governance`, `qualification`, `project` e `spine`). A implementação G3
  continua isolada e não foi promovida por incompatibilidade arquitetural.
- G1 na linha de auditoria antes desta mudança: `BLOCKED_BY_PACKAGING`. A revisão `acd90a27` não
  possui `pyproject.toml`, `setup.py` ou `setup.cfg`, nem entrypoint público
  `codepro`; portanto ainda não existe um artefato instalável para validar
  como produto. `tools/check_foundation.py`: `PASS` — 8 arquivos e 14
  invariantes. A suíte da biblioteca: `367` testes, `PASS`, em Python 3.13
  com `TEMP` controlado. A execução sem esse controle teve `49` erros de ACL;
  foi classificada como limitação de ambiente e não como aprovação.
- implementação inicial do limite G1 nesta linha: contrato registrado em
  `docs/decisions/0031-package-boundary-and-distribution.md`, distribuição
  `codepro==0.3.0.dev0`, namespace `arkx`, sem dependências de runtime. Em
  Python 3.13, wheel e sdist foram construídos; o wheel foi instalado em venv
  limpo sem `PYTHONPATH`, `arkx` importou, o baseline passou, o foundation
  check passou e a suíte passou com `367` testes. Hashes: wheel
  `B0EC4466576D6CFB52FD354451E7FD6BBB1AAEB4CC38D0134F530EEC00C22F2B`;
  sdist `72832FCE71C474DEB4DC68D18D4A20B5A69986CE450718AC44C8980A4A53029D`.
  O sdist também foi instalado em um segundo venv Python 3.13 sem
  `PYTHONPATH`; import, baseline e foundation check passaram. Isso é evidência
  local de distribuição, ainda sem aceitação independente.
- entrypoint público mínimo na linha atual: decisão `0032`, com apenas
  `codepro --version`, `codepro doctor [--json]` e `codepro baseline`; nenhum
  comando de tarefa ou executor foi adicionado. Testes focados: `4/4`, `PASS`.
  No wheel instalado em venv Python 3.13, sem `PYTHONPATH`, os três comandos
  passaram e a suíte completa passou com `371` testes, `OK`. Hash do wheel
  desta revisão: `0A983984D1B3207ABA689712147EEBFA978A2513619AEE6F36E7C7B1406FC36C`.
  O sdist da mesma revisão também foi instalado e executou os três comandos;
  hash `3E5C84BC4F601E672E834303BBE7AB2914FCD13658E846EF0FE4D0D27A4F2094`.
  Isso satisfaz a evidência local inicial de G3, mas ainda exige aceitação
  independente e não qualifica executor.
- fronteira negativa do G3: teste explícito confirma que `codepro run` é
  rejeitado (`SystemExit 2`, `invalid choice`); não há submissão silenciosa de
  tarefa. O focused suite passou com `5/5` e a suíte completa desta revisão
  passou com `372` testes, `OK`.
- automação adicionada em `.github/workflows/foundation.yml`: job
  `packaged-cli` constrói o wheel, instala em venv, verifica `--version`,
  `doctor --json`, `baseline` e executa a suíte sem `PYTHONPATH`. A alteração
  foi validada localmente por comandos equivalentes, mas o job GitHub ainda é
  `NOT_EXECUTED` até uma execução CI observável.
- reprodutibilidade do commit rastreado: `git archive` de `7e4b510a` foi
  extraído sem arquivos não rastreados; o wheel foi construído e instalado em
  venv limpo, `codepro --version`, `doctor --json` e `baseline` passaram, e a
  suíte passou com `372` testes, `OK`. Hash do wheel desse archive:
  `89E4C6DCA68F2BE494EC4EF2FD82AC859F6773A5DC3548B5F423BC5AF887B091`.
- execução CI externa do commit `2206e3cb`: `BLOCKED_INFRA`. Os jobs
  `foundation` e `packaged-cli` foram criados, mas nenhum passo iniciou; o
  GitHub registrou falha de pagamentos recentes ou limite de spending da conta.
  Isso não é aprovação nem reprovação funcional. A aceitação externa só pode
  ser repetida após a correção de Billing & Plans/spending limit.
- verificação local de artefatos da revisão seguinte: `python -m build` gerou
  wheel e sdist; `twine check` aprovou ambos; instalação do wheel em venv
  separado e `pip check` retornaram `No broken requirements found`. O workflow
  foi fortalecido para executar esses mesmos checks, mas essa alteração ainda
  aguarda CI externo após o desbloqueio da conta.
- revisão benchmark-driven do governance boundary: SWE-bench e
  Terminal-Bench exigem identidade de revisão, ambiente e verificador. O
  chassi agora bloqueia request sem `environment.workspace` ou
  `environment.revision`; o focused suite de request passou `9/9` e a suíte
  completa passou `373` testes. Isso fortalece reprodutibilidade e falha
  fechada, mas não qualifica executor nem demonstra resolução de tarefa.
- melhoria benchmark-driven do verificador: `TestResult` agora preserva
  `command`, `exit_code` e `duration_ms` quando observados, com validação de
  metadados inválidos. O focused suite de verification passou `14/14` e a
  suíte completa passou `375` testes. Esses campos tornam o verificador
  auditável; ainda precisam ser preenchidos por uma execução real no M1.
- boundary neutro de verificação implementado: `run_verification_command`
  executa argv declarado com `shell=False`, workspace existente e timeout;
  captura stdout/stderr, exit code e duração, e classifica timeout, executável
  ausente e erro de invocação como `UNKNOWN` explícito. Testes focados: `5/5`;
  suíte completa anterior: `380` testes, `OK`. Isso fecha a execução de
  comando do verificador, mas o vínculo a um executor real ainda pertence ao
  M1.
- persistência do verificador implementada em `VerificationEvidenceStore` e
  adaptador `CommandVerifier`: stdout/stderr, resultado e erro bruto são
  armazenados por identidade `run_id`/teste; conteúdo divergente para a mesma
  identidade bloqueia em vez de sobrescrever. A suíte focada do verificador e
  da orquestração passou `32/32` em Python 3.11. A suíte completa em Python
  3.13 continua `INDETERMINATE/ENVIRONMENT_ERROR` neste host por ACL do
  diretório temporário (56 falhas de permissão, incluindo cleanup); isso não é
  contado como PASS e exige repetição em um ambiente gravável.

## Primeiro trabalho autorizado pelo plano

O próximo trabalho é fechar M0/M1 do MVP: ligar request autorizado, workspace,
executor escolhido, verificador neutro e persistência de evidência em uma
jornada real. A aceitação independente, CI externo e promoção continuam
obrigatórios antes de qualquer release. Nenhuma alegação de executor ou
release de produto será feita antes desses gates.
