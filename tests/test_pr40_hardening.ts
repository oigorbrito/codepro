import {
  validateRepositoryRelativePath,
  normalizeCandidateFiles,
  checkScopeInclusion,
  validateOutcomeEvidence,
} from '../src/chassis/localizationPolicy';
import { executeVertical } from '../src/chassis/vertical';
import { reviewM1Evidence, M1_CONSTANTS } from '../src/chassis/m1Acceptance';

console.log('--- TEST 1: Path Lexical Policy (ADR 0159 / 0161) ---');
// 1.1 Valid relative paths
const p1 = validateRepositoryRelativePath('src/arkx/cli.py');
if (!p1.valid || p1.normalized !== 'src/arkx/cli.py') {
  throw new Error(`Expected valid normalized path, got ${JSON.stringify(p1)}`);
}

// 1.2 Redundant ./ prefix normalized
const p2 = validateRepositoryRelativePath('./src/arkx/cli.py');
if (!p2.valid || p2.normalized !== 'src/arkx/cli.py') {
  throw new Error(`Expected normalized without ./, got ${JSON.stringify(p2)}`);
}

// 1.3 Backslash normalized to POSIX /
const p3 = validateRepositoryRelativePath('src\\arkx\\cli.py');
if (!p3.valid || p3.normalized !== 'src/arkx/cli.py') {
  throw new Error(`Expected POSIX normalization, got ${JSON.stringify(p3)}`);
}

// 1.4 Non-drive colon preserved
const p4 = validateRepositoryRelativePath('module:submodule.py');
if (!p4.valid || p4.normalized !== 'module:submodule.py') {
  throw new Error(`Expected non-drive colon preserved, got ${JSON.stringify(p4)}`);
}

// 1.5 Absolute path rejected
const p5 = validateRepositoryRelativePath('/etc/passwd');
if (p5.valid) {
  throw new Error('Expected absolute path to be rejected');
}

// 1.6 Traversal rejected
const p6 = validateRepositoryRelativePath('../secret.ts');
if (p6.valid) {
  throw new Error('Expected traversal path to be rejected');
}
const p6b = validateRepositoryRelativePath('src/../../secret.ts');
if (p6b.valid) {
  throw new Error('Expected nested traversal path to be rejected');
}

// 1.7 Trailing separator rejected (concrete file, not directory)
const p7 = validateRepositoryRelativePath('src/arkx/');
if (p7.valid) {
  throw new Error('Expected trailing slash to be rejected');
}

// 1.8 Windows drive path rejected
const p8 = validateRepositoryRelativePath('C:/Windows/System32');
if (p8.valid) {
  throw new Error('Expected drive path to be rejected');
}

console.log('--- TEST 2: Scope Inclusion (NO_SILENT_SCOPE_EXPANSION) ---');
const scope = ['src/arkx/cli.py', 'tests/test_cli.py'];

// 2.1 Valid inclusion
const scopeOk = checkScopeInclusion(['src/arkx/cli.py'], scope);
if (!scopeOk.inScope || scopeOk.outOfScope.length > 0) {
  throw new Error(`Expected inScope=true, got ${JSON.stringify(scopeOk)}`);
}

// 2.2 Scope expansion rejected
const scopeViolation = checkScopeInclusion(['src/arkx/cli.py', 'package.json'], scope);
if (scopeViolation.inScope || !scopeViolation.outOfScope.includes('package.json')) {
  throw new Error(`Expected out-of-scope package.json, got ${JSON.stringify(scopeViolation)}`);
}

console.log('--- TEST 3: Positive Outcome Evidence Guard (ADR 0157) ---');
// 3.1 Missing authority rejected
const guardNoAuth = validateOutcomeEvidence('VERIFIED', '', 'evidence://run-1');
if (guardNoAuth.valid) {
  throw new Error('Expected rejection when authority is empty');
}

// 3.2 Missing evidence reference for positive outcome rejected
const guardNoEv = validateOutcomeEvidence('VERIFIED', 'user-authority', '');
if (guardNoEv.valid) {
  throw new Error('Expected rejection when positive outcome lacks evidence');
}

// 3.3 Valid positive outcome accepted
const guardOk = validateOutcomeEvidence('VERIFIED', 'user-authority', 'evidence://run-1');
if (!guardOk.valid) {
  throw new Error('Expected valid outcome evidence to pass');
}

console.log('--- TEST 4: Vertical Journey Scope Enforcement ---');
const vertRunResult = executeVertical({
  workspace: '/workspace',
  revision: 'e401936979aea7f875508394aab1dac8f9e850d0',
  request_id: 'req-test-pr40',
  task_id: 'task-test-pr40',
  requester_ref: 'authority://test',
  authority_ref: 'authority://test',
  acceptance_authority_ref: 'authority://test',
  scope: ['src/arkx/cli.py'],
  candidate_files: ['src/arkx/cli.py', 'malicious_tamper.ts'], // Out of scope
  affected_components: ['cli'],
  characterization_source_ref: 'test',
  max_wall_time_seconds: 60,
  attempt_id: 'attempt-1',
  executor_argv: ['echo', 'test'],
  verifier_argv: ['echo', 'verify'],
});

if (vertRunResult.status !== 'REJECTED') {
  throw new Error(`Expected REJECTED for scope expansion, got ${vertRunResult.status}`);
}
console.log('Vertical journey correctly REJECTED scope violation:', vertRunResult.reason);

console.log('--- TEST 5: M1 Acceptance Review Hardening ---');
// 5.1 Acceptance review fails if run_id is missing (ADR 0157)
const m1MissingRun = reviewM1Evidence({
  classification: 'M1_REAL_VERTICAL_VERIFIED',
  task_ref: M1_CONSTANTS.TASK_REF,
  request_id: M1_CONSTANTS.REQUEST_ID,
  task_id: M1_CONSTANTS.TASK_ID,
  target_base_sha: M1_CONSTANTS.BASE_SHA,
  provider_called: false,
  model_called: false,
  promotion: 'NOT_AUTHORIZED',
  executor: {
    id: 'local-command',
    selection: 'EXPLICIT',
    fallback_allowed: false,
  },
  observed_changed_files: [...M1_CONSTANTS.SCOPE],
  vertical_result: {
    run_id: '', // missing evidence run_id
    status: 'VERIFIED',
  },
});

if (m1MissingRun.decision !== 'REJECTED') {
  throw new Error('Expected M1 review to REJECT when evidence run_id is missing');
}
console.log('M1 Acceptance correctly REJECTED missing evidence run_id');

console.log('--- ALL ISSUE #40 / PR40 TESTS PASSED SUCCESSFULLY ---');
