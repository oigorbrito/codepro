/**
 * Evidence-only acceptance review for CodePro M1 task.
 */

export interface M1ReviewEvidence {
  classification?: string;
  task_ref?: string;
  request_id?: string;
  task_id?: string;
  target_base_sha?: string;
  provider_called?: boolean;
  model_called?: boolean;
  promotion?: string;
  executor?: {
    id?: string;
    selection?: string;
    fallback_allowed?: boolean;
  };
  observed_changed_files?: string[];
  steps?: {
    target_status_before?: { returncode?: number; stdout?: string };
    diff_check?: { returncode?: number };
    target_head?: { returncode?: number; stdout?: string };
    target_status_after?: { returncode?: number };
  };
  vertical_result?: {
    run_id?: string;
    status?: string;
  };
}

export interface AcceptanceDecision {
  decision: "ACCEPTED" | "REJECTED";
  status: string;
  reason: string;
  failures: string[];
  reviewed_at: string;
  acceptance_record: Record<string, unknown>;
}

export const M1_CONSTANTS = {
  TASK_REF: "github://oigorbrito/codepro/issues/57",
  REQUEST_ID: "m1-doctor-json-1",
  TASK_ID: "issue-57-doctor-json",
  BASE_SHA: "e401936979aea7f875508394aab1dac8f9e850d0",
  SCOPE: ["src/arkx/cli.py", "tests/test_cli.py"],
};

export function reviewM1Evidence(summary: M1ReviewEvidence): AcceptanceDecision {
  const failures: string[] = [];

  if (summary.classification !== "M1_REAL_VERTICAL_VERIFIED") {
    failures.push(`Expected classification M1_REAL_VERTICAL_VERIFIED, got ${summary.classification}`);
  }
  if (summary.task_ref !== M1_CONSTANTS.TASK_REF) {
    failures.push(`Task ref mismatch: expected ${M1_CONSTANTS.TASK_REF}, got ${summary.task_ref}`);
  }
  if (summary.request_id !== M1_CONSTANTS.REQUEST_ID) {
    failures.push(`Request ID mismatch: expected ${M1_CONSTANTS.REQUEST_ID}, got ${summary.request_id}`);
  }
  if (summary.task_id !== M1_CONSTANTS.TASK_ID) {
    failures.push(`Task ID mismatch: expected ${M1_CONSTANTS.TASK_ID}, got ${summary.task_id}`);
  }
  if (summary.target_base_sha !== M1_CONSTANTS.BASE_SHA) {
    failures.push(`Target base SHA mismatch: expected ${M1_CONSTANTS.BASE_SHA}, got ${summary.target_base_sha}`);
  }
  if (summary.provider_called !== false) {
    failures.push("Provider was called (forbidden under frozen provider-free evaluation)");
  }
  if (summary.model_called !== false) {
    failures.push("Model was called (forbidden under deterministic M1 criteria)");
  }
  if (summary.promotion !== "NOT_AUTHORIZED") {
    failures.push("Promotion must remain NOT_AUTHORIZED at M1 stage");
  }

  const executor = summary.executor || {};
  if (executor.id !== "local-command") {
    failures.push(`Executor ID must be local-command, got ${executor.id}`);
  }
  if (executor.selection !== "EXPLICIT") {
    failures.push("Executor selection must be EXPLICIT");
  }
  if (executor.fallback_allowed !== false) {
    failures.push("Fallback must be strictly disabled");
  }

  const observed = [...(summary.observed_changed_files || [])].sort();
  const expectedScope = [...M1_CONSTANTS.SCOPE].sort();
  if (JSON.stringify(observed) !== JSON.stringify(expectedScope)) {
    failures.push(`Observed changed files [${observed.join(", ")}] do not match exact scope [${expectedScope.join(", ")}]`);
  }

  const vertStatus = summary.vertical_result?.status;
  if (vertStatus !== "VERIFIED") {
    failures.push(`Vertical status is ${vertStatus}, expected VERIFIED`);
  }

  const isAccepted = failures.length === 0;

  return {
    decision: isAccepted ? "ACCEPTED" : "REJECTED",
    status: isAccepted ? "M1_INDEPENDENT_ACCEPTED" : "M1_REJECTED",
    reason: isAccepted
      ? "All deterministic M1 independent acceptance criteria verified without re-executing task."
      : `Acceptance criteria failed: ${failures.join("; ")}`,
    failures,
    reviewed_at: new Date().toISOString(),
    acceptance_record: {
      chassis: "codepro",
      review_authority: "acceptance://independent-local-auditor",
      verified_evidence_ref: summary.vertical_result?.run_id || "m1-run-evidence",
      criteria_checked: 12,
      criteria_passed: 12 - failures.length,
      failures,
    },
  };
}
