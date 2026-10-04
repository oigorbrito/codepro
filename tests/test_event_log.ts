import {
  EventLogBuilder,
  audit_restored_chain,
  ChainIntegrity,
  ChainedEvent,
} from '../src/chassis/eventLog';

console.log('--- TEST 1: Empty chain -> EMPTY ---');
const emptyAudit = audit_restored_chain([]);
console.log('Result:', emptyAudit.integrity);
if (emptyAudit.integrity !== ChainIntegrity.EMPTY) {
  throw new Error(`Expected EMPTY, got ${emptyAudit.integrity}`);
}

console.log('--- TEST 2: Valid chain -> COMPLETE ---');
const builder = new EventLogBuilder();
builder.append('TASK_STARTED', { request_id: 'req-1', task_id: 'task-1' });
builder.append('EXECUTOR_STARTED', { executor_id: 'gemini-2.5-flash' });
builder.append('TASK_FINISHED', { status: 'PASS', ref: 'verif-hash-abc' });

const chain = builder.buildChain();
const validAudit = audit_restored_chain([...chain.events]);
console.log('Result:', validAudit.integrity, 'Head digest:', validAudit.head_digest);
if (validAudit.integrity !== ChainIntegrity.COMPLETE) {
  throw new Error(`Expected COMPLETE, got ${validAudit.integrity}`);
}

const dict = chain.to_dict();
console.log('Event count:', dict.event_count);
console.log('Verification ref (absent stage):', dict.verification_ref);
console.log('Acceptance ref (absent stage):', dict.acceptance_ref);
console.log('Promotion ref (absent stage):', dict.promotion_ref);

console.log('--- TEST 3: Tampered payload -> TAMPERED ---');
const tamperedEvents: ChainedEvent[] = JSON.parse(JSON.stringify(chain.events));
// Modify payload of event 1
tamperedEvents[1].payload = { executor_id: 'tampered-executor' };
const tamperedAudit = audit_restored_chain(tamperedEvents);
console.log('Result:', tamperedAudit.integrity, 'Failures:', tamperedAudit.failures);
if (tamperedAudit.integrity !== ChainIntegrity.TAMPERED) {
  throw new Error(`Expected TAMPERED, got ${tamperedAudit.integrity}`);
}

console.log('--- TEST 4: Broken sequence order -> INVALID ---');
const invalidEvents: ChainedEvent[] = JSON.parse(JSON.stringify(chain.events));
invalidEvents[1].sequence = 5; // skip sequence
const invalidAudit = audit_restored_chain(invalidEvents);
console.log('Result:', invalidAudit.integrity, 'Failures:', invalidAudit.failures);
if (invalidAudit.integrity !== ChainIntegrity.INVALID) {
  throw new Error(`Expected INVALID, got ${invalidAudit.integrity}`);
}

console.log('--- ALL ADR 0164 CONTRACT TESTS PASSED ---');
