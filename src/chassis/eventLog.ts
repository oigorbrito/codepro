/**
 * CodePro ADR 0164: Event-Log Contract v1.1
 * Normative decision: SHA-256 canonical hash-chained audit trail.
 */

// 1. Exception Taxonomy
export class EventLogError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'EventLogError';
  }
}

export class EventLogFormatError extends EventLogError {
  constructor(message: string) {
    super(message);
    this.name = 'EventLogFormatError';
  }
}

export class EventLogIntegrityError extends EventLogError {
  constructor(message: string) {
    super(message);
    this.name = 'EventLogIntegrityError';
  }
}

// 2. Chain Integrity Enum
export enum ChainIntegrity {
  COMPLETE = 'COMPLETE',
  EMPTY = 'EMPTY',
  INVALID = 'INVALID',
  TAMPERED = 'TAMPERED',
}

// 3. Event Interface
export interface ChainedEvent {
  sequence: number;
  event_type: string;
  payload: Record<string, unknown>;
  previous_digest: string | null;
  digest: string;
}

// 4. SHA-256 & Canonical JSON Implementation (Zero-dependency, browser + node compatible)
function rightRotate(value: number, amount: number): number {
  return (value >>> amount) | (value << (32 - amount));
}

const K = [
  0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
  0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
  0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
  0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
  0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
  0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
  0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
  0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
];

export function sha256Utf8(str: string): string {
  const bytes = new TextEncoder().encode(str);
  let H = [
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
  ];
  const l = bytes.length;
  const bitLen = l * 8;
  const newLen = ((l + 9 + 63) >> 6) << 6;
  const padded = new Uint8Array(newLen);
  padded.set(bytes);
  padded[l] = 0x80;
  const view = new DataView(padded.buffer);
  view.setUint32(newLen - 4, bitLen >>> 0, false);
  view.setUint32(newLen - 8, Math.floor(bitLen / 0x100000000), false);

  const W = new Uint32Array(64);
  for (let i = 0; i < newLen; i += 64) {
    for (let t = 0; t < 16; t++) {
      W[t] = view.getUint32(i + t * 4, false);
    }
    for (let t = 16; t < 64; t++) {
      const s0 = rightRotate(W[t - 15], 7) ^ rightRotate(W[t - 15], 18) ^ (W[t - 15] >>> 3);
      const s1 = rightRotate(W[t - 2], 17) ^ rightRotate(W[t - 2], 19) ^ (W[t - 2] >>> 10);
      W[t] = (W[t - 16] + s0 + W[t - 7] + s1) >>> 0;
    }
    let [a, b, c, d, e, f, g, h] = H;
    for (let t = 0; t < 64; t++) {
      const S1 = rightRotate(e, 6) ^ rightRotate(e, 11) ^ rightRotate(e, 25);
      const ch = (e & f) ^ ((~e) & g);
      const temp1 = (h + S1 + ch + K[t] + W[t]) >>> 0;
      const S0 = rightRotate(a, 2) ^ rightRotate(a, 13) ^ rightRotate(a, 22);
      const maj = (a & b) ^ (a & c) ^ (b & c);
      const temp2 = (S0 + maj) >>> 0;

      h = g;
      g = f;
      f = e;
      e = (d + temp1) >>> 0;
      d = c;
      c = b;
      b = a;
      a = (temp1 + temp2) >>> 0;
    }
    H = [
      (H[0] + a) >>> 0, (H[1] + b) >>> 0, (H[2] + c) >>> 0, (H[3] + d) >>> 0,
      (H[4] + e) >>> 0, (H[5] + f) >>> 0, (H[6] + g) >>> 0, (H[7] + h) >>> 0
    ];
  }
  return H.map(x => x.toString(16).padStart(8, '0')).join('');
}

/**
 * Canonical UTF-8 JSON serialization matching Python sort_keys=True, separators=(",", ":"), ensure_ascii=False
 */
export function canonicalJsonStringify(obj: unknown): string {
  if (obj === null || typeof obj !== 'object') {
    return JSON.stringify(obj);
  }
  if (Array.isArray(obj)) {
    return '[' + obj.map((item) => canonicalJsonStringify(item)).join(',') + ']';
  }
  const keys = Object.keys(obj as Record<string, unknown>).sort();
  const pairs = keys.map((key) => {
    return JSON.stringify(key) + ':' + canonicalJsonStringify((obj as Record<string, unknown>)[key]);
  });
  return '{' + pairs.join(',') + '}';
}

/**
 * Computes canonical digest for an event (excluding the digest field itself)
 */
export function computeEventDigest(
  sequence: number,
  event_type: string,
  payload: Record<string, unknown>,
  previous_digest: string | null
): string {
  const canonicalRepresentation = canonicalJsonStringify({
    event_type,
    payload,
    previous_digest,
    sequence,
  });
  return sha256Utf8(canonicalRepresentation);
}

// 5. EventChain Class with v1.1 stage references
export class EventChain {
  readonly events: readonly ChainedEvent[];

  constructor(events: ChainedEvent[]) {
    this.events = Object.freeze([...events]);
  }

  get event_count(): number {
    return this.events.length;
  }

  get head_digest(): string | null {
    if (this.events.length === 0) return null;
    return this.events[this.events.length - 1].digest;
  }

  get verification_ref(): string | null {
    const stageEvent = this.events.find((e) => e.event_type === 'VERIFICATION_FINISHED' || e.event_type === 'VERIFIED');
    if (stageEvent && typeof stageEvent.payload.ref === 'string' && stageEvent.payload.ref.trim().length > 0) {
      return stageEvent.payload.ref.trim();
    }
    return null;
  }

  get acceptance_ref(): string | null {
    const stageEvent = this.events.find((e) => e.event_type === 'ACCEPTANCE_FINISHED' || e.event_type === 'ACCEPTED');
    if (stageEvent && typeof stageEvent.payload.ref === 'string' && stageEvent.payload.ref.trim().length > 0) {
      return stageEvent.payload.ref.trim();
    }
    return null;
  }

  get promotion_ref(): string | null {
    const stageEvent = this.events.find((e) => e.event_type === 'PROMOTION_FINISHED' || e.event_type === 'PROMOTED');
    if (stageEvent && typeof stageEvent.payload.ref === 'string' && stageEvent.payload.ref.trim().length > 0) {
      return stageEvent.payload.ref.trim();
    }
    return null;
  }

  to_dict(): {
    events: readonly ChainedEvent[];
    event_count: number;
    head_digest: string | null;
    verification_ref: string | null;
    acceptance_ref: string | null;
    promotion_ref: string | null;
  } {
    return {
      events: this.events,
      event_count: this.event_count,
      head_digest: this.head_digest,
      verification_ref: this.verification_ref,
      acceptance_ref: this.acceptance_ref,
      promotion_ref: this.promotion_ref,
    };
  }
}

// 6. ReplayAudit Structure
export interface ReplayAudit {
  run_id?: string;
  integrity: ChainIntegrity;
  event_count: number;
  head_digest: string | null;
  chain: EventChain | null;
  failures: string[];
}

/**
 * audit_restored_chain loads events, validates schema and ordering,
 * recalculates hashes, validates links, builds the chain, and returns the audit.
 * It returns COMPLETE only when all checks pass.
 * EMPTY, INVALID, and TAMPERED are never COMPLETE.
 */
export function audit_restored_chain(
  rawEvents: unknown[],
  options?: { run_id?: string }
): ReplayAudit {
  const failures: string[] = [];

  // Check 1: Zero events -> EMPTY (never COMPLETE)
  if (!Array.isArray(rawEvents) || rawEvents.length === 0) {
    return {
      run_id: options?.run_id,
      integrity: ChainIntegrity.EMPTY,
      event_count: 0,
      head_digest: null,
      chain: new EventChain([]),
      failures: ['Zero events present: chain is EMPTY'],
    };
  }

  const validatedEvents: ChainedEvent[] = [];
  let currentIntegrity = ChainIntegrity.COMPLETE;

  for (let i = 0; i < rawEvents.length; i++) {
    const ev = rawEvents[i] as Partial<ChainedEvent>;

    // Schema Validation -> INVALID
    if (typeof ev !== 'object' || ev === null) {
      failures.push(`Event at index ${i} is not a valid object`);
      return {
        run_id: options?.run_id,
        integrity: ChainIntegrity.INVALID,
        event_count: rawEvents.length,
        head_digest: null,
        chain: null,
        failures,
      };
    }

    if (typeof ev.sequence !== 'number' || typeof ev.event_type !== 'string' || typeof ev.payload !== 'object' || ev.payload === null) {
      failures.push(`Event at index ${i} has invalid schema (sequence, event_type, or payload missing/invalid)`);
      return {
        run_id: options?.run_id,
        integrity: ChainIntegrity.INVALID,
        event_count: rawEvents.length,
        head_digest: null,
        chain: null,
        failures,
      };
    }

    // Sequence continuity check: starts at 0, strictly contiguous -> INVALID
    if (ev.sequence !== i) {
      failures.push(`Sequence continuity failure at index ${i}: expected ${i}, got ${ev.sequence}`);
      return {
        run_id: options?.run_id,
        integrity: ChainIntegrity.INVALID,
        event_count: rawEvents.length,
        head_digest: null,
        chain: null,
        failures,
      };
    }

    // Predecessor link check: first event has null previous_digest, others reference previous event's digest
    if (i === 0) {
      if (ev.previous_digest !== null) {
        failures.push(`First event (sequence 0) must have null previous_digest, got ${ev.previous_digest}`);
        currentIntegrity = ChainIntegrity.TAMPERED;
      }
    } else {
      const prev = validatedEvents[i - 1];
      if (ev.previous_digest !== prev.digest) {
        failures.push(`Predecessor link mismatch at sequence ${i}: expected ${prev.digest}, got ${ev.previous_digest}`);
        currentIntegrity = ChainIntegrity.TAMPERED;
      }
    }

    // Recalculate hash over canonical representation
    const expectedDigest = computeEventDigest(
      ev.sequence,
      ev.event_type,
      ev.payload as Record<string, unknown>,
      ev.previous_digest ?? null
    );

    if (ev.digest !== expectedDigest) {
      failures.push(`Digest mismatch at sequence ${i}: expected ${expectedDigest}, got ${ev.digest}`);
      currentIntegrity = ChainIntegrity.TAMPERED;
    }

    validatedEvents.push({
      sequence: ev.sequence,
      event_type: ev.event_type,
      payload: ev.payload as Record<string, unknown>,
      previous_digest: ev.previous_digest ?? null,
      digest: ev.digest || expectedDigest,
    });
  }

  const chain = new EventChain(validatedEvents);

  return {
    run_id: options?.run_id,
    integrity: currentIntegrity,
    event_count: chain.event_count,
    head_digest: chain.head_digest,
    chain,
    failures,
  };
}

/**
 * EventLogBuilder helper to construct an immutable, valid hash chain step-by-step
 */
export class EventLogBuilder {
  private events: ChainedEvent[] = [];

  append(event_type: string, payload: Record<string, unknown>): ChainedEvent {
    const sequence = this.events.length;
    const previous_digest = sequence === 0 ? null : this.events[sequence - 1].digest;
    const digest = computeEventDigest(sequence, event_type, payload, previous_digest);

    const event: ChainedEvent = {
      sequence,
      event_type,
      payload,
      previous_digest,
      digest,
    };

    this.events.push(event);
    return event;
  }

  buildChain(): EventChain {
    return new EventChain(this.events);
  }
}
