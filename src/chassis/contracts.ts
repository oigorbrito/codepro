/**
 * Versioned, serializable contracts for CodePro P0 execution telemetry.
 */

export const SCHEMA_VERSION = 1;
export const CHASSIS_VERSION = "0.3.0";
export const CHASSIS_FINGERPRINT = "codepro-chassis-v0.3.0-deterministic-telemetry";

export enum ExecutionStatus {
  PASS = "PASS",
  FAILED = "FAILED",
  BLOCKED = "BLOCKED",
  INVALID = "INVALID",
  NOT_EXECUTED = "NOT_EXECUTED",
  UNVERIFIED = "UNVERIFIED",
}

export enum EventType {
  TASK_STARTED = "TASK_STARTED",
  EXECUTOR_STARTED = "EXECUTOR_STARTED",
  EXECUTOR_FINISHED = "EXECUTOR_FINISHED",
  RETRY = "RETRY",
  REPLAN = "REPLAN",
  HANDOFF = "HANDOFF",
  EVIDENCE_ADDED = "EVIDENCE_ADDED",
  HUMAN_INTERVENTION = "HUMAN_INTERVENTION",
  TASK_FINISHED = "TASK_FINISHED",
}

export interface TelemetryEvent {
  timestamp: string;
  type: EventType;
  run_id: string;
  data: Record<string, unknown>;
}

export interface TaskRequestPayload {
  request_id: string;
  task_id: string;
  requester_ref: string;
  authority_ref: string;
  acceptance_authority_ref: string;
  scope: string[];
  candidate_files: string[];
  affected_components: string[];
  characterization_source_ref: string;
  max_wall_time_seconds: number;
  attempt_id: string;
  executor_argv: string[];
  verifier_argv: string[];
}

export function validateEvent(event: TelemetryEvent): void {
  if (!event.timestamp || typeof event.timestamp !== "string") {
    throw new Error("timestamp must be a valid ISO string");
  }
  if (!event.run_id || typeof event.run_id !== "string") {
    throw new Error("run_id must be a non-blank string");
  }
  if (!Object.values(EventType).includes(event.type)) {
    throw new Error(`invalid event type: ${event.type}`);
  }
  if (typeof event.data !== "object" || event.data === null) {
    throw new Error("data must be an object");
  }
}

// Re-export ADR 0164 Event-Log Contract v1.1
export * from "./eventLog";

// Re-export ADR 0156-0161 Localization Policy & Scope Guard
export * from "./localizationPolicy";

// Re-export Gates M2 & M3 Validation Harness
export * from "./m2m3Validation";

// Re-export ADR 0152 Second Executor Qualification Harness
export * from "./secondExecutorQualification";

