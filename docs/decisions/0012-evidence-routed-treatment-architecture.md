# Arkx — Arquitetura Canônica Orientada por Tratamentos e Evidência

## Status

**Proposta canônica para as fases P8.2 → P8.4**

Esta decisão consolida a arquitetura que emergiu da evidência retrospectiva e do desenho experimental atual do Arkx.

Ela substitui uma interpretação simplificada em que o sistema seria apenas um router entre múltiplos executores.

O princípio arquitetural permanece:

> **minimum sufficient architecture for maximum reliable capability**

Os invariantes continuam válidos:

* `NO_COMPONENT_HAS_TENURE`
* `SCIENTIFIC_SIGNAL != LOCAL_PASS`
* `HYPOTHESIS != IMPLEMENTATION`
* `IMPLEMENTATION != EXECUTED`
* `EXECUTED != ACCEPTED`
* `ACCEPTED != PROMOTED`
* `DONOR != DEPENDENCY`
* `MECHANISM_PASS != EXECUTOR_ADOPTED`
* `BLOCKED != PASS`
* `NOT_EXECUTED != PASS`
* `NO_SILENT_FALLBACK`
* `NO_SILENT_EXECUTOR_SWITCH`
* `NO_SILENT_SCOPE_EXPANSION`

E as regras operacionais permanecem:

* `ROUTE BEFORE CASCADING`
* `DECOMPOSE ONLY WHEN JUSTIFIED`
* `ESCALATE ON EVIDENCE`
* `VERIFY BEFORE ACCEPTING`

---

## Decisão

A arquitetura do Arkx deve rotear primariamente para **regimes de tratamento**, e não diretamente para executores.

O executor é uma implementação de capacidade dentro de um tratamento.

A arquitetura canônica é:

```text
                         REQUEST
                            │
                            ▼
                GOVERNANCE / AUTHORITY
                            │
                            ▼
                 TASK CHARACTERIZATION
                            │
                            ▼
                          ROUTE
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
           SIMPLE        LOCALIZED     REPOSITORY-
            PATH         TREATMENT      WIDE PATH
              │             │             │
              │        localizer /     planning +
              │         verifier          state
              │             │             │
              └─────────────┴──────┬──────┘
                                   │
                                   ▼
                               EXECUTOR
                                   │
                                   ▼
                               PROGRESS?
                              /         \
                           yes           no
                            │             │
                            │        recover /
                            │         replan /
                            │         escalate
                            │             │
                            └──────┬──────┘
                                   │
                                   ▼
                                VERIFY
                                   │
                                   ▼
                        INDEPENDENT ACCEPTANCE
```

Essa estrutura deve ser considerada a referência arquitetural para as próximas fases do projeto.

---

## 1. Request

`REQUEST` representa a intenção externa submetida ao Arkx.

Ela ainda não constitui autorização para executar qualquer transformação.

A existência de uma request não implica:

```text
REQUEST != AUTHORITY
```

---

## 2. Governance / Authority

Governance ocorre antes de characterization, routing e execução.

Sua responsabilidade é definir os limites sob os quais a request pode ser processada.

Pode incluir:

* escopo autorizado;
* permissões;
* budgets;
* limites de tempo;
* restrições de ambiente;
* políticas de modificação;
* critérios de verification;
* definição da acceptance authority;
* invariantes aplicáveis.

O executor não deve definir retrospectivamente o que constitui sucesso.

```text
EXECUTOR OUTPUT != ACCEPTANCE AUTHORITY
```

---

## 3. Task Characterization

`TASK CHARACTERIZATION` descreve a tarefa antes da escolha do regime operacional.

Seu propósito não é simplesmente selecionar um executor.

Ela deve produzir evidência útil para determinar **qual tratamento é necessário**.

Características possíveis incluem:

* escopo provável da alteração;
* concentração/localização do problema;
* necessidade de exploração;
* necessidade de contexto de repositório;
* dependências entre arquivos/componentes;
* necessidade de planejamento;
* dificuldade de verification;
* histórico relevante;
* sinais conhecidos de falha ou sucesso de mecanismos.

A characterization deve ser separada da decisão de routing.

---

## 4. Route

O primeiro problema de routing é:

```text
WHAT TREATMENT DOES THIS TASK REQUIRE?
```

e não:

```text
WHICH AGENT SHOULD RUN?
```

O router deve selecionar o regime mínimo plausivelmente suficiente.

Isso preserva o princípio:

```text
minimum sufficient architecture
```

e evita pagar por coordenação, planejamento, contexto ou chassis adicionais em tarefas que não os exigem.

---

# Regimes de tratamento

## 5. Simple Path

O `SIMPLE PATH` é o caminho mínimo.

Destina-se a tarefas nas quais não exista evidência suficiente para justificar mecanismos adicionais.

Exemplo conceitual:

```text
TASK
  ↓
minimal context
  ↓
executor
  ↓
verify
  ↓
accept
```

O simple path deve minimizar:

* coordenação;
* contexto adicional;
* planejamento explícito;
* múltiplos agentes;
* ferramentas especializadas;
* overhead de execução.

O executor baseline esperado atualmente é o `mini-SWE-agent`, sujeito à qualificação experimental.

Baseline não implica tenure.

---

## 6. Localized Treatment

O `LOCALIZED TREATMENT` é usado quando existe evidência de que a principal dificuldade está em localizar, editar ou verificar uma região relativamente restrita do problema.

Pode incorporar mecanismos como:

* melhor localization;
* contextual retrieval dirigido;
* structural/repository search;
* safe editing;
* verification localizada;
* dependency context estritamente necessário.

Conceitualmente:

```text
TASK
  ↓
localize
  ↓
targeted context
  ↓
executor
  ↓
targeted verification
```

O objetivo não é introduzir um novo chassis quando um mecanismo pequeno consegue comprar a capacidade necessária.

Essa é precisamente uma das perguntas de P8.2:

```text
CAN A SMALL MECHANISM RECOVER CAPABILITY
WITHOUT IMPORTING A LARGER EXECUTOR?
```

---

## 7. Repository-Wide Path

O `REPOSITORY-WIDE PATH` é reservado para tarefas em que a evidência indique necessidade de capacidade transversal.

Pode incluir:

* planejamento explícito;
* manutenção de estado;
* dependency reasoning;
* architecture context;
* exploração de múltiplas regiões;
* decomposição;
* coordenação de subproblemas;
* recovery/replanning mais sofisticado.

Esse caminho pode justificar um executor/chassis especializado caso os experimentos demonstrem capacidade confiável que o baseline enriquecido não consegue reproduzir de maneira mais simples.

Portanto:

```text
REPOSITORY_WIDE != AUTOMATIC_MULTI_AGENT
```

e:

```text
COMPLEX TASK != AUTOMATIC_SPECIALIZED_EXECUTOR
```

É necessário demonstrar capability gap.

---

# Executor como implementação, não como eixo primário

## 8. Executor Placement

O executor ocorre **depois da seleção do tratamento**.

Isso é uma decisão arquitetural importante.

O Arkx não deve ser modelado primariamente como:

```text
ROUTER
 ├── mini
 ├── Moatless
 ├── OpenHands
 └── Lingxi
```

A representação preferida é:

```text
ROUTER
  │
  ├── SIMPLE PATH
  │      └── executor apropriado
  │
  ├── LOCALIZED TREATMENT
  │      ├── mechanisms
  │      └── executor apropriado
  │
  └── REPOSITORY-WIDE PATH
         ├── planning/state
         └── executor apropriado
```

Executores são candidatos a implementar capacidades dentro desses regimes.

Eles não constituem, por si só, a taxonomia arquitetural.

---

# Progress, recovery e escalation

## 9. Progress / Stagnation

Depois da execução começar, o Arkx deve observar progresso.

A questão não é apenas se o executor terminou.

Devem existir sinais capazes de distinguir, quando possível:

* progresso;
* exploração repetitiva;
* ausência de avanço;
* regressão;
* edit failure;
* verification failure;
* necessidade de replan;
* necessidade de escalation.

Conceitualmente:

```text
EXECUTOR
   │
   ▼
PROGRESS?
 /      \
yes      no
 │        │
 │      recover
 │      replan
 │      escalate
 │        │
 └────────┘
```

Escalation não deve equivaler a cascade automática.

```text
EXECUTOR_A FAILED
    !=
RUN EXECUTOR_B AUTOMATICALLY
```

O segundo executor somente deve ser introduzido quando exista evidência de que outro tratamento ou capability é justificável.

Isso preserva:

```text
ROUTE BEFORE CASCADING
ESCALATE ON EVIDENCE
```

---

# Verification e acceptance

## 10. Verification

Verification avalia propriedades técnicas observáveis da solução.

Pode incluir:

* patch validity;
* testes;
* regressões;
* estrutura do diff;
* artifacts;
* reprodução do problema;
* checks específicos.

Verification não possui autoridade automática para promoção ou acceptance.

```text
VERIFICATION_PASS != ACCEPTED
```

---

## 11. Independent Acceptance

Acceptance deve permanecer uma autoridade separada do executor.

O executor não pode declarar sua própria solução aceita.

A cadeia conceitual permanece:

```text
IMPLEMENTED
   ↓
EXECUTED
   ↓
VERIFIED
   ↓
ACCEPTED
   ↓
potential evidence for future promotion
```

Nenhuma transição é implícita.

Acceptance pode produzir estados como:

```text
ACCEPTED
REJECTED
INDETERMINATE
BLOCKED
NOT_EXECUTED
```

Estados desconhecidos ou não executados não devem ser reduzidos a booleanos.

---

# Relação com P8.2

## 12. O significado de A/B/C/D

Os tratamentos experimentais de P8.2 não são quatro arquiteturas candidatas.

Eles são intervenções destinadas a isolar efeitos de mecanismos.

Atualmente:

```text
A = mini baseline

B = mini + safe editor

C = mini + enhanced repository context

D = mini + safe editor + enhanced repository context
```

O objetivo é separar:

```text
MODEL_EFFECT
SCAFFOLD_EFFECT
MECHANISM_EFFECT
MODEL × SCAFFOLD INTERACTION
```

e, especificamente em P8.2, produzir evidência sobre `MECHANISM_EFFECT`.

Os resultados devem ajudar a responder quais mecanismos pertencem ao:

```text
SIMPLE PATH
```

quais justificam:

```text
LOCALIZED TREATMENT
```

e quais capacidades permanecem ausentes e podem exigir:

```text
REPOSITORY-WIDE PATH
```

---

# Relação com P8.3

## 13. Targeted Executor Qualification

P8.3 não deve ser tratado como um torneio geral de agentes.

Seu propósito é investigar capabilities que continuem não satisfeitas após P8.2.

Os candidatos registrados atualmente incluem:

* mini enriquecido;
* Moatless;
* OpenHands;
* Lingxi;
* SWE-agent como controle quando informativo;
* candidatos adicionais evidence-qualified.

A pergunta para cada challenger deve ser:

```text
WHAT UNIQUE RELIABLE CAPABILITY DOES THIS EXECUTOR BUY?
```

e não:

```text
WHICH EXECUTOR HAS THE HIGHEST GLOBAL SCORE?
```

Um chassis adicional somente se justifica se adquirir capacidade útil que não possa ser absorvida mais economicamente como mecanismo.

---

# Relação com P8.4

## 14. Routed Composition

P8.4 deverá validar a composição seletiva.

O objetivo não é:

```text
mini
  ↓ fail
SWE-agent
  ↓ fail
OpenHands
  ↓ fail
...
```

Esse desenho violaria `ROUTE BEFORE CASCADING`.

A composição desejada é aproximadamente:

```text
REQUEST
   ↓
GOVERNANCE
   ↓
CHARACTERIZE
   ↓
ROUTE
   │
   ├── SIMPLE
   │
   ├── LOCALIZED
   │
   └── REPOSITORY-WIDE
   │
   ↓
SELECT SUFFICIENT EXECUTOR/CAPABILITY
   ↓
EXECUTE
   ↓
PROGRESS / STAGNATION
   ↓
VERIFY
   ↓
INDEPENDENT ACCEPTANCE
```

Um segundo executor só deve aparecer mediante evidência.

Essa direção já estava estabelecida no protocolo de composição seletiva do projeto.

---

# Interpretação da evidência existente

## 15. Complementaridade não implica arquitetura multiagente

A evidência retrospectiva mostrou discordância relevante entre executores.

No conjunto comparável registrado:

* 262 tasks foram resolvidas por todos;
* 93 falharam para todos;
* 145 apresentaram discordância;
* a união oracle atingiu 407/500, ou 81,4%.

Isso demonstra que `EXECUTOR CHOICE CONTAINS SIGNAL`, mas não demonstra que oracle routing seja realizável.

Portanto, a consequência arquitetural não é:

```text
RUN MORE AGENTS
```

A consequência é:

```text
IDENTIFY THE SIGNAL
       ↓
CHARACTERIZE THE TASK
       ↓
ROUTE TO THE MINIMUM SUFFICIENT CAPABILITY
```

---

# Consequências arquiteturais

## 16. Mecanismos podem substituir chassis

Se P8.2 demonstrar que mecanismos pequenos recuperam capacidade que parecia exclusiva de chassis maiores:

```text
ABSORB THE MECHANISM
```

em vez de:

```text
ADOPT THE CHASSIS
```

Isso reduz:

* dependências;
* manutenção;
* complexidade de routing;
* custo operacional;
* superfície de falha;
* dificuldade de observabilidade.

---

## 17. Specialized executors permanecem permitidos

A arquitetura não proíbe múltiplos executores.

Ela exige evidência para cada um.

Um executor especializado permanece justificável quando:

```text
SPECIALIZED_EXECUTOR
    BUYS
UNIQUE + RELIABLE + USEFUL CAPABILITY
```

que não seja economicamente reproduzida pelo baseline enriquecido.

---

## 18. Arquitetura pode encolher com a evidência

O objetivo de P8 não é necessariamente adicionar componentes.

Um resultado válido de P8 pode ser remover candidatos.

A arquitetura final pode acabar contendo:

```text
1 baseline executor
+
small proven mechanisms
+
1 specialized executor
```

ou até menos, caso isso seja suficiente.

Também pode justificar mais componentes se os experimentos demonstrarem necessidade.

Não existe quantidade pré-determinada de agentes ou executores.

---

# Progressão arquitetural

A progressão correta das fases é:

```text
P8.1
QUALIFICATION CONTRACTS
        │
        ▼
P8.2
ISOLATE MECHANISM EFFECT
        │
        ▼
DISCOVER REQUIRED PATH CAPABILITIES
        │
        ▼
P8.3
TARGETED EXECUTOR QUALIFICATION
        │
        ▼
P8.4
SELECTIVE ROUTED COMPOSITION
        │
        ▼
MINIMUM SUFFICIENT ARKX ARCHITECTURE
```

P8.2 deve acontecer antes de importar novos chassis justamente para determinar se mecanismos comprovados podem ser absorvidos de forma mais barata. Essa é a direção científica registrada do projeto:

```text
ABSORB PROVEN MECHANISMS WHEN CHEAPER

KEEP SPECIALIZED EXECUTORS ONLY WHEN THEY BUY
UNIQUE RELIABLE CAPABILITY

DO NOT LIMIT THE SEARCH TO WESTERN MODELS
OR THE THREE OBVIOUS EXECUTORS
```

---

# Arquitetura canônica resumida

```text
REQUEST
   │
   ▼
GOVERNANCE / AUTHORITY
   │
   ▼
TASK CHARACTERIZATION
   │
   ▼
ROUTE BY REQUIRED CAPABILITY
   │
   ├──────────────┬────────────────────┐
   │              │                    │
   ▼              ▼                    ▼
SIMPLE         LOCALIZED          REPOSITORY-WIDE
PATH           TREATMENT              PATH
   │              │                    │
   │          mechanisms         planning / state /
   │          as justified       deeper capability
   │              │                    │
   └──────────────┴─────────┬──────────┘
                            │
                            ▼
                     SUFFICIENT EXECUTOR
                            │
                            ▼
                     PROGRESS / STAGNATION
                            │
                ┌───────────┴───────────┐
                │                       │
            progress              insufficient
                │                       │
                │              recover / replan /
                │                  escalate
                │                       │
                └───────────┬───────────┘
                            │
                            ▼
                         VERIFY
                            │
                            ▼
                  INDEPENDENT ACCEPTANCE
                            │
                            ▼
                     EVIDENCE / DONE
```

## Regra final

O Arkx não deve perguntar primeiro:

```text
WHICH AGENT?
```

Deve perguntar:

```text
WHAT CAPABILITY DOES THIS TASK REQUIRE?
```

Depois:

```text
WHAT IS THE MINIMUM TREATMENT THAT PROVIDES IT?
```

E somente então:

```text
WHICH EXECUTOR CAN DELIVER THAT TREATMENT
RELIABLY AND ECONOMICALLY?
```

Essa é a interpretação arquitetural que melhor preserva, no estado atual do projeto, a evidência acumulada e o princípio de **minimum sufficient architecture for maximum reliable capability**.
