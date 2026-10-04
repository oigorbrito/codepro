import {
  EXECUTOR_REGISTRY,
  runQualifiedTaskCell,
  runPairedQualificationComparison,
} from '../src/chassis/secondExecutorQualification';
import { ISSUE_57_FROZEN_SPEC } from '../src/chassis/m2m3Validation';

console.log('--- TEST 1: Verificar Registro de Candidatos e Preflight ---');

const miniSwe = EXECUTOR_REGISTRY['mini-swe-agent'];
const geminiExec = EXECUTOR_REGISTRY['gemini-structured-code-agent'];
const openhands = EXECUTOR_REGISTRY['openhands-cli'];

if (miniSwe.qualification_status !== 'QUALIFIED') {
  throw new Error('mini-swe-agent deve ser QUALIFIED');
}
if (geminiExec.qualification_status !== 'QUALIFIED') {
  throw new Error('gemini-structured-code-agent deve ser QUALIFIED');
}
if (openhands.qualification_status !== 'QUALIFIED') {
  throw new Error('openhands-cli deve ser QUALIFIED após criação do ~/.openhands');
}
console.log('1.1 Candidatos mapeados e OpenHands desbloqueado no ambiente local.');

console.log('--- TEST 2: Célula de Execução Individual dos Executores ---');
const primaryRun = runQualifiedTaskCell('mini-swe-agent', 'test-p1');
if (primaryRun.status !== 'VERIFIED' || primaryRun.task_id !== ISSUE_57_FROZEN_SPEC.TASK_ID) {
  throw new Error(`Erro na execução do primary executor: ${JSON.stringify(primaryRun)}`);
}
console.log('2.1 Primary executor executou a tarefa #57 com status VERIFIED.');

const secondaryRun = runQualifiedTaskCell('gemini-structured-code-agent', 'test-s1');
if (secondaryRun.status !== 'VERIFIED' || secondaryRun.task_id !== ISSUE_57_FROZEN_SPEC.TASK_ID) {
  throw new Error(`Erro na execução do secondary executor: ${JSON.stringify(secondaryRun)}`);
}
console.log('2.2 Secondary executor aprovado executou a mesma tarefa #57 com status VERIFIED.');

console.log('--- TEST 3: Execução da Comparação Pareada Oficial (ADR 0152) ---');
const pairedReport = runPairedQualificationComparison();

if (pairedReport.classification !== 'PAIRED_QUALIFICATION_SUCCESS') {
  throw new Error(`Esperado PAIRED_QUALIFICATION_SUCCESS, recebido ${pairedReport.classification}`);
}
if (!pairedReport.parity_checks.both_verified) {
  throw new Error('Ambos os executores devem alcançar status VERIFIED');
}
if (!pairedReport.parity_checks.distinct_executor_identities) {
  throw new Error('Identidades dos executores devem ser estritamente segregadas');
}
if (!pairedReport.parity_checks.same_scope) {
  throw new Error('Ambos os executores devem respeitar o mesmo conjunto de escopo');
}

console.log('3.1 Classificação Pareada:', pairedReport.classification);
console.log('3.2 Ambas as células VERIFIED sob mesmo escopo e verifier:', pairedReport.parity_checks.both_verified);
console.log('3.3 Decision Basis validado conforme AGENTS.md:', pairedReport.decision_record.basis_type);

console.log('--- TODOS OS TESTES DO 2º EXECUTOR PASSARAM COM SUCESSO ---');
