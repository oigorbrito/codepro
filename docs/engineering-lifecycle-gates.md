# Portões do Ciclo de Vida de Engenharia

Este repositório utiliza portões de ciclo de vida baseados em evidências para evitar a declaração de que um projeto, MVP, lançamento ou implantação em produção está pronto com base apenas na intuição.

O processo é fundamentado em práticas consolidadas de engenharia de software e desenvolvimento seguro, incluindo:

- ISO/IEC/IEEE 12207 — processos de ciclo de vida de software
- ISO/IEC 25010 — qualidade de produto de software
- ISO/IEC/IEEE 29119 — processos de teste de software
- NIST Secure Software Development Framework (SSDF)
- OpenSSF OSPS Baseline
- Pesquisas de entrega de software DORA
- Controles de repositório e lançamento do GitHub

Essas fontes orientam o processo. Os requisitos de produto específicos do projeto determinam quais recursos de produto são realmente necessários.

---

# 1. Semântica de evidências

Cada verificação aplicável deve ser resolvida exatamente em um dos seguintes estados:

- `PASS` (Aprovado) — a evidência foi realmente obtida.
- `FAIL` (Reprovado) — a evidência demonstra que o requisito não foi atendido.
- `BLOCKED` (Bloqueado) — a verificação não pôde ser concluída devido a uma dependência externa ou ambiental.
- `NOT_VERIFIED` (Não verificado) — a verificação ainda não foi executada.
- `NOT_APPLICABLE` (Não aplicável) — o requisito não se aplica, acompanhado de uma justificativa explícita.

Nunca interprete evidências ausentes, ignoradas, presumidas, indisponíveis ou bloqueadas como `PASS`.

Um portão de ciclo de vida é aprovado apenas quando todos os requisitos obrigatórios aplicáveis forem resolvidos como `PASS`.

---

# 2. Contrato do produto

Antes de avaliar a maturidade do ciclo de vida, determine o que o produto realmente é.

Declarações obrigatórias:

- usuário primário;
- problema sendo resolvido;
- jornada do usuário primário;
- interfaces necessárias;
- mecanismo de entrega;
- requisitos de persistência de dados;
- dependências/provedores externos;
- não-objetivos explícitos.

Interfaces possíveis incluem:

- CLI (Interface de Linha de Comando);
- Web UI (Interface Web);
- HTTP/API;
- biblioteca/pacote;
- UI de desktop (Interface Desktop);
- worker/serviço em segundo plano;
- integração máquina-a-máquina (M2M).

Mecanismos de entrega possíveis incluem:

- código-fonte;
- executável;
- pacote;
- container;
- serviço hospedado (SaaS);
- aplicativo móvel.

Não invente uma interface apenas porque ela é comum.

Se a aplicabilidade de uma interface de produto importante permanecer indefinida, reporte:

`PRODUCT_CONTRACT_INCOMPLETE`

e solicite essa decisão antes de utilizar sua ausência como um defeito.

---

# 3. Portão de BOOTSTRAP (Inicialização)

Objetivo: estabelecer contexto de produto e engenharia suficiente para iniciar o trabalho sem criar arquitetura acidental.

Requisitos:

- [ ] o propósito do produto está documentado;
- [ ] o usuário primário está definido;
- [ ] a jornada do usuário primário está definida;
- [ ] as interfaces necessárias estão declaradas;
- [ ] o mecanismo de entrega está declarado ou explicitamente indefinido;
- [ ] as principais dependências externas foram identificadas;
- [ ] os não-objetivos explícitos estão registrados;
- [ ] instruções canônicas do repositório existem;
- [ ] existe um comando canônico ou procedimento documentado para verificação, mesmo que inicialmente minimalista.

Sucesso:

`BOOTSTRAP_READY = YES`

A prontidão para bootstrap não significa que o aplicativo já funciona.

---

# 4. Portão de EXECUTÁVEL

Objetivo: provar que o projeto não é mais apenas código-fonte ou design.

Requisitos:

- [ ] um ambiente limpo/novo consegue obter o código-fonte;
- [ ] as dependências necessárias podem ser instaladas ou provisionadas;
- [ ] o projeto pode ser compilado/iniciado/importado conforme apropriado;
- [ ] a interface primária exigida torna-se acessível;
- [ ] uma operação bem-sucedida mínima funciona;
- [ ] as falhas são observáveis em vez de silenciosamente ignoradas;
- [ ] as instruções de execução correspondem à implementação atual.

Exemplos por perfil de produto:

## CLI (Linha de Comando)

Verificar, quando aplicável:

- instalação;
- invocação do executável;
- ajuda (`help`);
- informações de versão, se versionado;
- comando principal / caminho feliz (happy path);
- comportamento com entradas inválidas;
- status de saída (exit code) significativo.

## Aplicação Web

Verificar:

- a aplicação inicia;
- o ponto de entrada acessível pelo navegador funciona;
- a página principal renderiza;
- o fluxo de usuário primário é executado;
- falhas de dependências de backend são observáveis.

## HTTP/API

Verificar:

- o serviço inicia;
- rotas de integridade/prontidão (health/readiness) conforme aplicável;
- requisição válida representativa;
- resposta esperada;
- requisição inválida/não autorizada representativa.

## Biblioteca

Verificar:

- o pacote é compilado;
- a instalação limpa é bem-sucedida;
- a importação é bem-sucedida;
- uma chamada de API pública representativa é bem-sucedida.

## Container/Serviço

Verificar:

- a imagem é gerada com sucesso;
- o container inicia;
- testes de integridade/prontidão funcionam onde aplicável;
- o comportamento do serviço primário pode ser exercitado.

Sucesso:

`EXECUTABLE_READY = YES`

---

# 5. Portão de CANDIDATO A MVP

Objetivo: demonstrar que a menor promessa de produto é realmente utilizável.

O MVP é definido pelo contrato do produto do projeto, não por uma contagem universal de recursos.

Requisitos:

- [ ] `EXECUTABLE_READY = YES`;
- [ ] todas as capacidades declaradas obrigatórias para o MVP existem;
- [ ] cada interface voltada para o usuário exigida é utilizável;
- [ ] a jornada do usuário primário funciona de ponta a ponta;
- [ ] caminhos de falha críticos possuem comportamento explícito;
- [ ] o comportamento de persistência/estado é verificado onde aplicável;
- [ ] fronteiras externas exigidas possuem substitutos determinísticos ou procedimentos de aceitação controlados;
- [ ] documentação básica do usuário existe;
- [ ] verificação automatizada existe para comportamentos críticos;
- [ ] as limitações conhecidas do MVP estão documentadas;
- [ ] nenhuma capacidade obrigatória do MVP é apenas presumida.

A ausência de um recurso opcional não reprova este portão.

A ausência de uma capacidade obrigatória de produto sim.

Sucesso:

`MVP_READY = YES`

---

# 6. Portão de QUALIDADE

Objetivo: atuar como o equivalente de software de uma inspeção independente.

Avaliar as características de qualidade aplicáveis, incluindo:

- adequação funcional;
- confiabilidade (reliability);
- eficiência de desempenho, onde relevante;
- usabilidade/capacidade de interação;
- compatibilidade/interoperabilidade;
- segurança;
- manutenibilidade;
- portabilidade/flexibilidade, onde relevante.

Não crie limites numéricos arbitrários.

Para cada propriedade de qualidade usada como critério de liberação, identifique:

1. requisito;
2. método de verificação;
3. evidência;
4. condição de aceitação.

Requisitos:

- [ ] requisitos críticos possuem evidência de aceitação;
- [ ] testes automatizados cobrem comportamentos determinísticos importantes;
- [ ] o comportamento de integração é testado na fronteira real de integração onde for prático;
- [ ] regressões possuem testes de regressão apropriados;
- [ ] fronteiras relevantes para a segurança possuem verificação explícita;
- [ ] falhas não resolvidas de alta consequência são registradas.

Sucesso:

`QUALITY_GATE = PASS`

---

# 7. Portão de RELEASE CANDIDATE (Candidato a Lançamento)

Objetivo: provar que um candidato específico e imutável pode ser entregue.

Requisitos:

- [ ] commit/revisão exata do candidato identificada;
- [ ] escopo planejado de lançamento documentado;
- [ ] versão/identificador de lançamento selecionado;
- [ ] o pipeline canônico de CI passa no candidato exato;
- [ ] compilação/empacotamento é bem-sucedido;
- [ ] o artefato de entrega real é produzido;
- [ ] o artefato de entrega real é testado com testes de fumaça (smoke tests);
- [ ] cada interface exigida do produto possui evidência de testes de fumaça relevantes para o lançamento;
- [ ] o procedimento de instalação/implantação é verificado onde aplicável;
- [ ] a documentação voltada para o usuário corresponde ao candidato;
- [ ] README/exemplos/comandos não descrevem comportamentos obsoletos;
- [ ] requisitos de dependências/compilação são identificáveis;
- [ ] verificações de segurança aplicáveis são aprovadas;
- [ ] limitações e defeitos conhecidos estão registrados;
- [ ] notas de lançamento (release notes) / changelog descrevem o candidato;
- [ ] não há itens pendentes explicitamente classificados como bloqueadores de lançamento;
- [ ] requisitos de rollback/recuperação estão definidos onde aplicável.

Não exija que todos os problemas (issues) ou pull requests do repositório estejam fechados.

Exija:

`OPEN_RELEASE_BLOCKERS = 0` (Zero bloqueadores de lançamento em aberto)

Sucesso:

`RELEASE_CANDIDATE_READY = YES`

---

# 8. Portão de RELEASE (Lançamento)

Objetivo: lançar exatamente o que foi verificado.

Requisitos:

- [ ] o portão de candidato a lançamento (Release Candidate) foi aprovado;
- [ ] a identidade do lançamento corresponde ao candidato testado;
- [ ] a tag/versão de lançamento aponta para a revisão imutável pretendida;
- [ ] os artefatos produzidos correspondem a essa revisão;
- [ ] as notas de lançamento correspondem a essa versão;
- [ ] evidências de integridade/proveniência são geradas onde aplicável;
- [ ] SBOM (Software Bill of Materials) é gerado onde aplicável;
- [ ] o artefato publicado é verificado após a publicação onde for prático;
- [ ] a evidência de lançamento é preservada.

Não recompile silenciosamente um artefato diferente após a qualificação.

Sucesso:

`SOFTWARE_RELEASED = YES`

---

# 9. Portão de PRODUÇÃO / ATIVAÇÃO

O lançamento do software (Release) e a ativação em produção são decisões separadas.

Requisitos quando aplicáveis:

- [ ] o artefato real lançado é selecionado;
- [ ] a configuração de produção é validada;
- [ ] segredos/credenciais são provisionados através de mecanismos aprovados;
- [ ] o princípio do menor privilégio é aplicado;
- [ ] o banco de dados / armazenamento de produção é provisionado;
- [ ] migrações são verificadas;
- [ ] rotas de integridade/prontidão funcionam;
- [ ] fronteiras de entrada/TLS/rede estão configuradas;
- [ ] a observabilidade necessária para a operação existe;
- [ ] o backup está configurado para dados persistentes críticos;
- [ ] o processo de restauração foi demonstrado onde a recuperação é importante;
- [ ] provedores externos são aceitos no ambiente de destino;
- [ ] aprovações operacionais/legais estão concluídas onde aplicável;
- [ ] o procedimento de rollback existe;
- [ ] os testes de fumaça em produção são aprovados.

Sucesso:

`PRODUCTION_READY = YES`

É perfeitamente válido ter:

`SOFTWARE_RELEASED = YES`

e:

`PRODUCTION_READY = NO`

---

# 10. Portão de MANUTENÇÃO

Verificar periodicamente:

- status de dependências e segurança;
- o pipeline de CI ainda executa os portões pretendidos;
- a documentação ainda corresponde à realidade;
- as versões suportadas estão explícitas;
- dependências/provedores externos não invalidaram premissas;
- backup/restauração permanecem viáveis;
- arquiteturas obsoletas ou mecanismos temporários foram identificados;
- a política de ciclo de vida / versão do pipeline permanece atualizada.

Registre desvios de forma explícita.

Estado possível:

`HARNESS_DRIFT = YES` (Desvio de conformidade detectado)

Isso não significa automaticamente que o software está com defeito, mas exige revisão.

---

# 11. Portão de ARQUIVAMENTO

Antes de declarar um projeto como arquivado:

- [ ] o estado final do repositório é identificado;
- [ ] a versão final suportada/lançada é identificada;
- [ ] limitações conhecidas e problemas não resolvidos são preservados;
- [ ] o status de suporte está explícito;
- [ ] evidências exigidas de origem/compilação/lançamento são preservadas;
- [ ] segredos e credenciais temporárias não foram deixados para trás;
- [ ] recursos de implantação obsoletos são tratados intencionalmente.

Sucesso:

`PROJECT_ARCHIVED = YES`

---

# 12. Regra de transição

Uma solicitação para avançar para um estado posterior do ciclo de vida ativa todos os portões predecessores exigidos.

Exemplos:

`preparar MVP`
→ avaliar os portões Bootstrap, Executável e MVP.

`preparar lançamento`
→ avaliar os portões predecessores exigidos mais Quality e Release Candidate.

`implantar em produção`
→ avaliar o portão Release mais Produção/Ativação.

Não pule portões predecessores reprovados apenas porque o usuário solicitou uma etapa posterior.

---

# 13. Regra da fonte da verdade

Três fontes de requisitos devem permanecer distintas:

## Requisito de produto

Define o que este produto em particular deve fazer.

Exemplo:

`web_ui = required` (Interface Web necessária)

## Requisito de engenharia/governança

Define como uma propriedade aplicável deve ser verificada ou controlada.

Exemplos:

- testes automatizados;
- integridade do lançamento;
- proteção da branch principal;
- controles de desenvolvimento seguro.

## Evidência

Prova se o requisito foi atendido.

Never convert uma categoria em outra.

Uma norma de governança não inventa recursos de produto.

Um requisito de produto não se prova sozinho.

Um agente de IA não substitui uma evidência física real.
