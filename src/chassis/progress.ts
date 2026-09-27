/**
 * Deterministic progress and stagnation assessment for P2.
 */

export enum ProgressStatus {
  CONFIRMED = "CONFIRMED",
  STAGNATED = "STAGNATED",
  BLOCKED = "BLOCKED",
  UNVERIFIED = "UNVERIFIED",
}

export interface ProgressAssessmentRequest {
  attempt_count: number;
  max_attempts: number;
  tests_passing: number;
  tests_failing: number;
  previous_tests_passing?: number;
  files_modified: number;
  churn_lines: number;
  last_output_summary?: string;
}

export interface ProgressAssessmentResult {
  status: ProgressStatus;
  can_continue: boolean;
  reasons: string[];
  remedy?: string;
}

export function assessProgress(req: ProgressAssessmentRequest): ProgressAssessmentResult {
  const reasons: string[] = [];

  if (req.attempt_count >= req.max_attempts) {
    reasons.push(`Budget exhausted: reached maximum attempt limit of ${req.max_attempts}`);
    return {
      status: ProgressStatus.BLOCKED,
      can_continue: false,
      reasons,
      remedy: "Escalate to human intervention or re-characterize scope.",
    };
  }

  const prevPass = req.previous_tests_passing ?? 0;
  if (req.tests_passing > prevPass) {
    reasons.push(`Progress verified: tests passing improved from ${prevPass} to ${req.tests_passing}`);
    return {
      status: ProgressStatus.CONFIRMED,
      can_continue: true,
      reasons,
    };
  }

  if (req.attempt_count > 1 && req.tests_passing <= prevPass && req.churn_lines > 100) {
    reasons.push("High code churn (>100 lines) without test progress detected");
    return {
      status: ProgressStatus.STAGNATED,
      can_continue: false,
      reasons,
      remedy: "Roll back speculative edits and restrict scope to candidate files.",
    };
  }

  if (req.files_modified === 0 && req.attempt_count > 1) {
    reasons.push("No workspace mutations observed across multiple attempts");
    return {
      status: ProgressStatus.STAGNATED,
      can_continue: false,
      reasons,
      remedy: "Verify executor environment and workspace write permissions.",
    };
  }

  reasons.push("Initial execution or steady state under evaluation");
  return {
    status: ProgressStatus.UNVERIFIED,
    can_continue: true,
    reasons,
  };
}
