# Portão de Prontidão para Lançamento (Release Readiness Gate)

Quando o usuário solicitar um lançamento (release), entrega, publicação, tag, empacotamento ou declarar o projeto pronto para um cliente, não deduza a prontidão apenas com base na conclusão da implementação.

Trate a prontidão para lançamento como um portão baseado em evidências.

## Procedimento obrigatório

1. Identifique o commit/versão exato do candidato e o escopo planejado do lançamento.

2. Determine a(s) interface(s) de produto realmente exposta(s) pelo projeto:
   - CLI (Interface de Linha de Comando)
   - API
   - GUI/Web UI (Interface Gráfica / Interface Web)
   - biblioteca/pacote
   - serviço
   - executável/ferramenta
   - outra interface declarada

3. Execute os procedimentos canônicos de compilação e verificação automatizada a partir de um estado limpo ou reproduzível.

4. Realize um teste de fumaça (smoke test) de cada interface primária voltada para o usuário.

   Exemplos:
   - CLI: verificar ajuda (`help`), versão, instalação e o caminho do comando principal.
   - API: iniciar o serviço e verificar uma requisição/resposta representativa.
   - UI: iniciar/compilar a aplicação e verificar o fluxo primário do usuário.
   - Biblioteca: instalar/importar o artefato empacotado e exercitar a API pública básica.

5. Verifique se a documentação voltada para o usuário reflete o lançamento do candidato:
   - instalação
   - configuração
   - funcionalidade básica
   - comandos/interfaces
   - exemplos
   - limitações conhecidas

   Não presuma que o README ou a documentação estão atualizados apenas porque existem.

6. Verifique os metadados do lançamento:
   - identificador de versão único
   - consistência da versão em locais relevantes do pacote/código/interface
   - notas de lançamento (release notes) ou changelog descrevendo mudanças funcionais e alterações de segurança relevantes

7. Verifique se as dependências e requisitos de compilação estão documentados e são reproduzíveis.

8. Realize a avaliação de segurança exigida pela linha de base atual de governança do repositório. Não dispense silenciosamente um controle de segurança aplicável.

9. Verifique o artefato real de entrega, e não apenas a árvore de código-fonte. Onde aplicável, verifique:
   - instalação limpa
   - comportamento do executável/pacote
   - integridade do artefato
   - assinaturas ou atestados
   - proveniência
   - SBOM (Software Bill of Materials / Lista de Materiais de Software)

10. Registre defeitos conhecidos, limitações, verificações puladas, verificações indisponíveis e bloqueadores externos.

## Semântica de evidências

Um requisito pode resultar apenas em:

- PASS (Aprovado) — a evidência exigida foi realmente obtida.
- FAIL (Reprovado) — a evidência mostra que o requisito não foi atendido.
- BLOCKED (Bloqueado) — a verificação não pôde ser executada devido a um bloqueador externo ou ambiental.
- NOT_APPLICABLE (Não aplicável) — o requisito não se aplica, acompanhado de uma justificativa explícita.
- NOT_VERIFIED (Não verificado) — a verificação não foi realizada.

Nunca converta verificações classificadas como BLOCKED, puladas, indisponíveis, presumidas ou não documentadas em PASS.

## Decisão de lançamento

Não publique, crie tags, faça upload, implante ou declare que o lançamento está pronto enquanto qualquer requisito obrigatório de lançamento estiver como FAIL, BLOCKED ou NOT_VERIFIED.

Produza um Relatório de Prontidão para Lançamento (Release Readiness Report) contendo:

- commit/versão candidato
- escopo do lançamento
- tipo de produto/interface
- verificações executadas
- evidência para cada resultado
- falhas/bloqueadores restantes
- limitações conhecidas
- resultado final `RELEASE_READY = YES | NO`

O resultado do CI/validador é soberano para portões executáveis. O julgamento do agente pode explicar as evidências, mas nunca deve anular um portão reprovado.

## Base de referência

Este portão de lançamento operacionaliza controles e práticas aplicáveis do:
- OpenSSF OSPS Baseline
- NIST Secure Software Development Framework (SSDF)
- Capacidades de entrega de software DORA
- Semântica de tags/lançamentos do GitHub

Requisitos específicos do repositório podem adicionar controles mais rígidos, mas nunca devem enfraquecer silenciosamente essas verificações de linha de base.
