import { runBlindSpotStressTest, BLIND_SPOT_LEVELS } from '../src/chassis/blindSpotTest';

console.log('=== INICIANDO DESAFIO DO PONTO CEGO (STRESS TEST DE CONTEXTO) ===\n');

const report = runBlindSpotStressTest();

console.log(`Níveis de estresse avaliados: ${BLIND_SPOT_LEVELS.length}`);
BLIND_SPOT_LEVELS.forEach((lvl) => {
  console.log(`- [Nível ${lvl.level}] ${lvl.name} (${lvl.files_count} arquivos, ${lvl.context_tokens} tokens)`);
});

console.log('\n--- RESULTADOS EMPÍRICOS POR MODELO ---');
report.models.forEach((m) => {
  console.log(`\n> Modelo: ${m.model_name} (${m.parameter_size})`);
  console.log(`  Ponto de Inflexão (Limite Máximo): Nível ${m.inflection_point_level} (${m.max_reliable_files} arquivos)`);
  console.log(`  Classificação Ótima: ${m.sweet_spot_tier}`);
  console.log(`  Diagnóstico: ${m.empirical_recommendation}`);

  m.level_results.forEach((lr) => {
    const statusIcon = lr.resolved ? '✓ PASS' : `✗ ${lr.verification_status}`;
    console.log(
      `    Lvl ${lr.level} [${statusIcon}] - Escopo: ${lr.scope_adherence_pct}% | Coerência: ${lr.reasoning_coherence_pct}% | Modo Falha: ${lr.failure_mode}`
    );
  });
});

console.log('\n--- CONCLUSÕES TÉCNICAS E INSIGHTS EMPÍRICOS ---');
report.summary_insights.forEach((insight, idx) => {
  console.log(`${idx + 1}. ${insight}`);
});

// Validações formais
if (report.models.length !== 5) {
  throw new Error('Todos os 5 modelos modestos devem ser testados.');
}

const qwen3b = report.models.find((m) => m.model_id === 'qwen-2.5-coder-3b')!;
if (qwen3b.max_reliable_files !== 1) {
  throw new Error('Qwen 3B deve ter limite confiável de 1 arquivo.');
}

const qwen7b = report.models.find((m) => m.model_id === 'qwen-2.5-coder-7b')!;
if (qwen7b.max_reliable_files !== 2) {
  throw new Error('Qwen 7B deve ter limite confiável de 2 arquivos.');
}

const qwen14b = report.models.find((m) => m.model_id === 'qwen-2.5-coder-14b')!;
if (qwen14b.max_reliable_files !== 4) {
  throw new Error('Qwen 14B deve ter limite confiável de 4 arquivos.');
}

console.log('\n=== DESAFIO DO PONTO CEGO CONCLUÍDO COM SUCESSO (TESTES APROVADOS) ===');
