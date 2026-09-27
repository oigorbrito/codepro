/**
 * Fail-closed TypeScript adapter for the authoritative Python vertical.
 *
 * React / Express
 *      ->
 * this adapter
 *      ->
 * explicit CODEPRO_PYTHON
 *      ->
 * python -m arkx run
 *      ->
 * arkx.vertical
 *
 * This module does not simulate executor output, changed files, verifier
 * results, qualification, acceptance, routing, fallback, or promotion.
 */

import { spawnSync } from "node:child_process";
import {
  existsSync,
  readdirSync,
  readFileSync,
  statSync,
} from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export interface VerticalRunInput {
  workspace: string;
  revision: string;
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

export type VerticalRunStatus =
  | "BLOCKED"
  | "EXECUTED"
  | "VERIFIED"
  | "REJECTED"
  | "FAILED"
  | "TIMED_OUT"
  | "ENVIRONMENT_UNAVAILABLE";

export interface VerticalRunResult {
  run_id: string;
  status: VerticalRunStatus;
  reason: string;
  evidence_root: string;
  changed_files: string[];
  attempt_id: string;

  /**
   * Adapter-observation metadata only.
   * Authoritative run evidence lives under evidence_root.
   */
  events: [];
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
}

const MODULE_DIR = path.dirname(fileURLToPath(import.meta.url));
const CODEPRO_SRC_DIR = path.resolve(MODULE_DIR, "..");

const VALID_STATUSES = new Set<VerticalRunStatus>([
  "BLOCKED",
  "EXECUTED",
  "VERIFIED",
  "REJECTED",
  "FAILED",
  "TIMED_OUT",
  "ENVIRONMENT_UNAVAILABLE",
]);

const MAX_CAPTURE_BYTES = 16 * 1024 * 1024;

function requireBinding(name: "CODEPRO_PYTHON" | "CODEPRO_EVIDENCE_DIR"): string {
  const value = process.env[name]?.trim();

  if (!value) {
    throw new Error(
      `${name} is required for the real vertical adapter; implicit fallback is disabled`,
    );
  }

  return value;
}

function requireString(value: unknown, field: string): string {
  if (typeof value !== "string" || value.trim() === "") {
    throw new Error(`${field} must be a non-empty string`);
  }

  return value;
}

function requireStringArray(
  value: unknown,
  field: string,
  options: { allowEmpty?: boolean } = {},
): string[] {
  if (!Array.isArray(value)) {
    throw new Error(`${field} must be a string array`);
  }

  if (!options.allowEmpty && value.length === 0) {
    throw new Error(`${field} must not be empty`);
  }

  if (value.some((item) => typeof item !== "string" || item.length === 0)) {
    throw new Error(`${field} must contain only non-empty strings`);
  }

  return [...value];
}

function parseCoreResult(
  raw: string,
  adapterObservation: {
    started_at: string | null;
    finished_at: string | null;
    duration_ms: number | null;
  },
): VerticalRunResult {
  let value: unknown;

  try {
    value = JSON.parse(raw);
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    throw new Error(`Python core returned invalid JSON: ${detail}`);
  }

  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error("Python core result must be a JSON object");
  }

  const record = value as Record<string, unknown>;

  const runId = requireString(record.run_id, "run_id");
  const statusRaw = requireString(record.status, "status");

  if (!VALID_STATUSES.has(statusRaw as VerticalRunStatus)) {
    throw new Error(`Python core returned unsupported status: ${statusRaw}`);
  }

  const reason = requireString(record.reason, "reason");
  const evidenceRoot = requireString(record.evidence_root, "evidence_root");
  const changedFiles = requireStringArray(
    record.changed_files,
    "changed_files",
    { allowEmpty: true },
  );
  const attemptId = requireString(record.attempt_id, "attempt_id");

  return {
    run_id: runId,
    status: statusRaw as VerticalRunStatus,
    reason,
    evidence_root: evidenceRoot,
    changed_files: changedFiles,
    attempt_id: attemptId,

    // No synthetic execution telemetry is generated here.
    events: [],
    started_at: adapterObservation.started_at,
    finished_at: adapterObservation.finished_at,
    duration_ms: adapterObservation.duration_ms,
  };
}

function pythonEnvironment(): NodeJS.ProcessEnv {
  const inherited = process.env.PYTHONPATH?.trim();

  return {
    ...process.env,

    /*
     * Deterministically bind python -m arkx to this CodePro source tree.
     * This is module binding, not executor/provider fallback.
     */
    PYTHONPATH: inherited
      ? `${CODEPRO_SRC_DIR}${path.delimiter}${inherited}`
      : CODEPRO_SRC_DIR,
  };
}

function appendRepeated(
  args: string[],
  flag: string,
  values: string[],
): void {
  for (const value of values) {
    args.push(flag, value);
  }
}

function evidenceDirectory(): string {
  return path.resolve(requireBinding("CODEPRO_EVIDENCE_DIR"));
}

function assertPersistedEvidence(
  result: VerticalRunResult,
  configuredEvidenceDir: string,
): void {
  const evidenceRoot = path.resolve(result.evidence_root);
  const relative = path.relative(configuredEvidenceDir, evidenceRoot);

  if (
    relative === "" ||
    relative.startsWith(`..${path.sep}`) ||
    relative === ".." ||
    path.isAbsolute(relative)
  ) {
    throw new Error(
      "Python core returned an evidence_root outside CODEPRO_EVIDENCE_DIR",
    );
  }

  const persistedResult = path.join(evidenceRoot, "result.json");

  if (!existsSync(persistedResult)) {
    throw new Error(
      `Python core did not persist expected evidence: ${persistedResult}`,
    );
  }
}

export function executeVertical(
  input: VerticalRunInput,
): VerticalRunResult {
  const python = requireBinding("CODEPRO_PYTHON");
  const evidenceDir = evidenceDirectory();

  const workspace = requireString(input.workspace, "workspace");
  const revision = requireString(input.revision, "revision");
  const requestId = requireString(input.request_id, "request_id");
  const taskId = requireString(input.task_id, "task_id");
  const requester = requireString(input.requester_ref, "requester_ref");
  const authority = requireString(input.authority_ref, "authority_ref");
  const acceptanceAuthority = requireString(
    input.acceptance_authority_ref,
    "acceptance_authority_ref",
  );

  const scope = requireStringArray(input.scope, "scope");
  const candidateFiles = requireStringArray(
    input.candidate_files,
    "candidate_files",
  );
  const affectedComponents = requireStringArray(
    input.affected_components,
    "affected_components",
  );
  const executorArgv = requireStringArray(
    input.executor_argv,
    "executor_argv",
  );
  const verifierArgv = requireStringArray(
    input.verifier_argv,
    "verifier_argv",
  );

  const characterizationSourceRef = requireString(
    input.characterization_source_ref,
    "characterization_source_ref",
  );

  const attemptId = requireString(input.attempt_id, "attempt_id");

  if (
    typeof input.max_wall_time_seconds !== "number" ||
    !Number.isFinite(input.max_wall_time_seconds) ||
    input.max_wall_time_seconds <= 0
  ) {
    throw new Error(
      "max_wall_time_seconds must be a finite positive number",
    );
  }

  const args: string[] = [
    "-m",
    "arkx",
    "run",
    "--workspace",
    workspace,
    "--revision",
    revision,
    "--request-id",
    requestId,
    "--task-id",
    taskId,
    "--requester",
    requester,
    "--authority",
    authority,
    "--acceptance-authority",
    acceptanceAuthority,
  ];

  appendRepeated(args, "--scope", scope);
  appendRepeated(args, "--candidate-file", candidateFiles);
  appendRepeated(args, "--affected-component", affectedComponents);

  args.push(
    "--characterization-source-ref",
    characterizationSourceRef,
    "--max-wall-time",
    String(input.max_wall_time_seconds),
    "--attempt-id",
    attemptId,
    "--evidence-dir",
    evidenceDir,
    "--verifier-argv-json",
    JSON.stringify(verifierArgv),
    "--",
    ...executorArgv,
  );

  const startedAt = new Date().toISOString();
  const startedMs = Date.now();

  const processResult = spawnSync(
    python,
    args,
    {
      encoding: "utf8",
      shell: false,
      env: pythonEnvironment(),
      maxBuffer: MAX_CAPTURE_BYTES,

      /*
       * The Python core owns executor/verifier wall-time semantics.
       * This outer bound only prevents an adapter process from hanging
       * indefinitely if the core itself becomes unavailable.
       */
      timeout: Math.ceil(
        (input.max_wall_time_seconds + 30) * 1000,
      ),
    },
  );

  const finishedMs = Date.now();
  const finishedAt = new Date().toISOString();

  if (processResult.error) {
    throw new Error(
      `Python vertical adapter failed: ${processResult.error.message}`,
    );
  }

  if (processResult.signal) {
    throw new Error(
      `Python vertical adapter terminated by signal ${processResult.signal}`,
    );
  }

  const stdout = processResult.stdout?.trim() ?? "";
  const stderr = processResult.stderr?.trim() ?? "";

  if (!stdout) {
    throw new Error(
      [
        "Python vertical produced no result JSON",
        `exit=${processResult.status ?? "unknown"}`,
        stderr ? `stderr=${stderr}` : "",
      ]
        .filter(Boolean)
        .join("; "),
    );
  }

  const result = parseCoreResult(stdout, {
    started_at: startedAt,
    finished_at: finishedAt,
    duration_ms: finishedMs - startedMs,
  });

  /*
   * codepro run exits:
   *   0 -> VERIFIED
   *   1 -> real non-VERIFIED run result
   *   2 -> invocation/configuration failure
   *
   * A status outside 0/1 is not converted into a fabricated run state.
   */
  if (processResult.status !== 0 && processResult.status !== 1) {
    throw new Error(
      [
        "Python core invocation failed before a valid run boundary completed",
        `exit=${processResult.status ?? "unknown"}`,
        stderr ? `stderr=${stderr}` : "",
      ]
        .filter(Boolean)
        .join("; "),
    );
  }

  assertPersistedEvidence(result, evidenceDir);

  return result;
}

function readPersistedResult(
  resultPath: string,
): VerticalRunResult {
  const raw = readFileSync(resultPath, "utf8");
  const parsed = parseCoreResult(raw, {
    started_at: null,
    finished_at: null,
    duration_ms: null,
  });

  return parsed;
}

export function getRunEvidence(
  runId: string,
): VerticalRunResult | undefined {
  if (!runId || path.basename(runId) !== runId) {
    return undefined;
  }

  const root = evidenceDirectory();
  const resultPath = path.join(root, runId, "result.json");

  if (!existsSync(resultPath)) {
    return undefined;
  }

  return readPersistedResult(resultPath);
}

export function listRunEvidence(): VerticalRunResult[] {
  const root = evidenceDirectory();

  if (!existsSync(root)) {
    return [];
  }

  const results: Array<{
    result: VerticalRunResult;
    mtimeMs: number;
  }> = [];

  for (const entry of readdirSync(root, { withFileTypes: true })) {
    if (!entry.isDirectory()) {
      continue;
    }

    const resultPath = path.join(root, entry.name, "result.json");

    if (!existsSync(resultPath)) {
      continue;
    }

    try {
      results.push({
        result: readPersistedResult(resultPath),
        mtimeMs: statSync(resultPath).mtimeMs,
      });
    } catch {
      /*
       * An invalid evidence directory is not promoted into valid evidence.
       * It is simply absent from the list endpoint; direct run execution
       * remains fail-closed.
       */
    }
  }

  return results
    .sort((a, b) => b.mtimeMs - a.mtimeMs)
    .map((item) => item.result);
}
