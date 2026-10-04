import {
  executeM2Scenario,
  runIssue57RepetitionCycle,
  validateM2M3Gate,
  ISSUE_57_FROZEN_SPEC,
} from '../src/chassis/m2m3Validation';

console.log('--- TEST 1: Gate M2 Negative Scenarios (Zero False Success) ---');

// 1.1 Nonzero exit
const r1 = executeM2Scenario({
  scenario: 'NONZERO_EXIT',
  task_id: ISSUE_57_FROZEN_SPEC.TASK_ID,
  scope: ISSUE_57_FROZEN_SPEC.SCOPE,
  candidate_files: ISSUE_57_FROZEN_SPEC.SCOPE,
});
if (r1.status !== 'FAILED' || !r1.non_zero_exit_detected || !r1.verified_prevented) {
  throw new Error(`Expected FAILED for nonzero exit, got ${JSON.stringify(r1)}`);
}
console.log('1.1 Nonzero exit correctly yielded FAILED (VERIFIED strictly prevented)');

// 1.2 Command timeout
const r2 = executeM2Scenario({
  scenario: 'COMMAND_TIMEOUT',
  task_id: ISSUE_57_FROZEN_SPEC.TASK_ID,
  scope: ISSUE_57_FROZEN_SPEC.SCOPE,
  candidate_files: ISSUE_57_FROZEN_SPEC.SCOPE,
});
if (r2.status !== 'TIMED_OUT' || !r2.timeout_detected || !r2.verified_prevented) {
  throw new Error(`Expected TIMED_OUT, got ${JSON.stringify(r2)}`);
}
console.log('1.2 Command timeout correctly yielded TIMED_OUT (VERIFIED strictly prevented)');

// 1.3 Environment unavailable
const r3 = executeM2Scenario({
  scenario: 'ENVIRONMENT_UNAVAILABLE',
  task_id: ISSUE_57_FROZEN_SPEC.TASK_ID,
  scope: ISSUE_57_FROZEN_SPEC.SCOPE,
  candidate_files: ISSUE_57_FROZEN_SPEC.SCOPE,
});
if (r3.status !== 'ENVIRONMENT_UNAVAILABLE' || !r3.env_unavailable_detected || !r3.verified_prevented) {
  throw new Error(`Expected ENVIRONMENT_UNAVAILABLE, got ${JSON.stringify(r3)}`);
}
console.log('1.3 Environment unavailable correctly yielded ENVIRONMENT_UNAVAILABLE');

console.log('--- TEST 2: Gate M3 Repetition of Frozen Issue #57 ---');

const cycle1 = runIssue57RepetitionCycle('attempt-1');
const cycle2 = runIssue57RepetitionCycle('attempt-2');

if (cycle1.status !== 'VERIFIED' || cycle2.status !== 'VERIFIED') {
  throw new Error('Both cycles must reach VERIFIED');
}
if (cycle1.attempt_id === cycle2.attempt_id) {
  throw new Error('Attempts must have distinct attempt_id');
}
if (cycle1.run_id === cycle2.run_id) {
  throw new Error('Runs must have distinct run_id / evidence root');
}
if (cycle1.base_sha !== cycle2.base_sha) {
  throw new Error('Base SHA must match');
}
if (cycle1.patch_sha256 !== cycle2.patch_sha256) {
  throw new Error(`Patch SHA mismatch: ${cycle1.patch_sha256} vs ${cycle2.patch_sha256}`);
}
console.log('2.1 Both cycles VERIFIED with distinct run_ids and identical patch SHA-256:', cycle1.patch_sha256);

console.log('--- TEST 3: Combined M2 + M3 Validation Gate ---');
const report = validateM2M3Gate();
if (report.classification !== 'M2_M3_VALIDATED') {
  throw new Error(`Expected M2_M3_VALIDATED, got ${report.classification}`);
}
console.log('3.1 Full Gate validation classification:', report.classification);
console.log('3.2 All negative states passed without false success:', report.m2_results.all_negative_passed);
console.log('3.3 Idempotent reproducibility validated:', report.m3_results.idempotent_reproducibility);

console.log('--- ALL ISSUE #57 / GATES M2 & M3 TESTS PASSED SUCCESSFULLY ---');
