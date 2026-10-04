import {
  TIERED_EXECUTOR_REGISTRY,
  routeTaskToTier,
} from '../src/chassis/tieredRouting';

console.log('--- TEST 1: Catálogo de Tiers e Benchmarks Empíricos ---');

const t1 = TIERED_EXECUTOR_REGISTRY.TIER_1_LIGHT;
const t2 = TIERED_EXECUTOR_REGISTRY.TIER_2_MEDIUM;
const t3 = TIERED_EXECUTOR_REGISTRY.TIER_3_HEAVY;

if (!t1.benchmark_evidence.some((b) => b.institution.includes('Princeton NLP'))) {
  throw new Error('Tier 1 deve conter evidência formal de benchmark do SWE-bench / Princeton NLP');
}
if (!t2.benchmark_evidence.some((b) => b.institution.includes('UC Berkeley') || b.institution.includes('Princeton NLP'))) {
  throw new Error('Tier 2 deve conter evidência formal de benchmark sério');
}
if (!t3.benchmark_evidence.some((b) => b.institution.includes('LMSYS') || b.institution.includes('Princeton NLP'))) {
  throw new Error('Tier 3 deve conter evidência formal de benchmark de raciocínio de ponta');
}

console.log('1.1 Tiers configurados com evidências de Princeton NLP, UC Berkeley e LMSYS Org.');

console.log('--- TEST 2: Roteamento de Tarefa Leve (Tier 1) ---');
const lightRoute = routeTaskToTier({
  task_title: 'Corrigir typo em argparse help',
  files_count: 1,
  lines_changed_estimate: 5,
  has_cross_module_dependency: false,
  is_structural_refactor: false,
});
if (lightRoute.selected_tier !== 'TIER_1_LIGHT') {
  throw new Error(`Esperado TIER_1_LIGHT, recebido ${lightRoute.selected_tier}`);
}
console.log('2.1 Tarefa pontual roteada para:', lightRoute.assigned_executor.underlying_model);

console.log('--- TEST 3: Roteamento de Tarefa Mediana (Tier 2) ---');
const medRoute = routeTaskToTier({
  task_title: 'Refatorar sincronização entre contracts.ts e eventLog.ts',
  files_count: 3,
  lines_changed_estimate: 75,
  has_cross_module_dependency: true,
  is_structural_refactor: false,
});
if (medRoute.selected_tier !== 'TIER_2_MEDIUM') {
  throw new Error(`Esperado TIER_2_MEDIUM, recebido ${medRoute.selected_tier}`);
}
console.log('3.1 Tarefa intermediária multi-módulo roteada para:', medRoute.assigned_executor.underlying_model);

console.log('--- TEST 4: Roteamento de Tarefa Complexa / Repo-Wide (Tier 3) ---');
const heavyRoute = routeTaskToTier({
  task_title: 'Reestruturar motor de persistência e isolamento de runtime no monorepo',
  files_count: 8,
  lines_changed_estimate: 450,
  has_cross_module_dependency: true,
  is_structural_refactor: true,
});
if (heavyRoute.selected_tier !== 'TIER_3_HEAVY') {
  throw new Error(`Esperado TIER_3_HEAVY, recebido ${heavyRoute.selected_tier}`);
}
console.log('4.1 Tarefa arquitetural pesada roteada para:', heavyRoute.assigned_executor.underlying_model);

console.log('--- TODOS OS TESTES DE ROTEAMENTO POR TIERS PASSARAM COM SUCESSO ---');
