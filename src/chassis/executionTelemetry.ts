/**
 * Normalized local-inference execution telemetry.
 *
 * This is specialized local-inference measurement evidence. It is not CodePro's canonical generic execution record.
 * Correlate it with arkx.contracts.ExecutionRecord by run_id. It does not imply verification,
 * acceptance, promotion, or executor qualification.
 */

import fs from "fs";
import path from "path";

export const LOCAL_INFERENCE_MEASUREMENT_SCHEMA_VERSION = 1 as const;
export const LOCAL_INFERENCE_MEASUREMENT_RECORD_TYPE = "LOCAL_INFERENCE_EXECUTION" as const;

export type InferenceDevice = "CPU" | "CUDA";

export interface LocalInferenceMeasurementRecordV1 {
  schema_version: typeof LOCAL_INFERENCE_MEASUREMENT_SCHEMA_VERSION;
  record_type: typeof LOCAL_INFERENCE_MEASUREMENT_RECORD_TYPE;
  run_id: string;
  captured_at: string;

  platform: {
    os: string;
    arch: string;
    gpu: string | null;
  };

  model: {
    repository: string;
    artifact: string | null;
    format: "GGUF";
    quantization: string;
  };

  runtime: {
    name: "llama.cpp";
    version: string;
    build: string;
    commit: string;
    executable_path: string;
  };

  execution: {
    device: InferenceDevice;
    device_id: string | null;
    context_length: number;
    max_generated_tokens: number;
    temperature: number;
    gpu_layers_requested: number;
    gpu_layers_offloaded: number;
    argv: string[];
  };

  metrics: {
    wall_time_ms: number;
    load_time_ms: number | null;
    peak_process_ram_mib: number;
    vram_baseline_mib: number | null;
    peak_vram_mib: number | null;
    vram_delta_mib: number | null;
    prompt_tokens_per_sec: number;
    generation_tokens_per_sec: number;
  };

  termination: {
    response_valid: boolean;
    expected_response: string | null;
    exit_code: number | null;
    reason: "COMPLETED" | "FAILED" | "INTERRUPTED" | "UNKNOWN";
  };

  cost: {
    provider_api_cost_usd: 0;
    local_compute_cost_usd: number | null;
  };

  evidence: {
    stdout_path: string;
    stderr_path: string;
    metrics_path: string;
  };
}

function requireNonBlank(value: string, field: string): void {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error(`${field} must be a non-blank string`);
  }
}

function requireFiniteNonNegative(value: number, field: string): void {
  if (!Number.isFinite(value) || value < 0) {
    throw new Error(`${field} must be a finite non-negative number`);
  }
}

function requireNullableFiniteNonNegative(
  value: number | null,
  field: string,
): void {
  if (value !== null) {
    requireFiniteNonNegative(value, field);
  }
}

export function validateLocalInferenceMeasurementRecord(record: LocalInferenceMeasurementRecordV1): void {
  if (record.schema_version !== LOCAL_INFERENCE_MEASUREMENT_SCHEMA_VERSION) {
    throw new Error("unsupported execution telemetry schema_version");
  }
  if (record.record_type !== LOCAL_INFERENCE_MEASUREMENT_RECORD_TYPE) {
    throw new Error("invalid execution telemetry record_type");
  }

  requireNonBlank(record.run_id, "run_id");
  requireNonBlank(record.captured_at, "captured_at");
  if (Number.isNaN(Date.parse(record.captured_at))) {
    throw new Error("captured_at must be an ISO-compatible timestamp");
  }

  requireNonBlank(record.platform.os, "platform.os");
  requireNonBlank(record.platform.arch, "platform.arch");

  requireNonBlank(record.model.repository, "model.repository");
  requireNonBlank(record.model.quantization, "model.quantization");

  requireNonBlank(record.runtime.version, "runtime.version");
  requireNonBlank(record.runtime.build, "runtime.build");
  requireNonBlank(record.runtime.commit, "runtime.commit");
  requireNonBlank(record.runtime.executable_path, "runtime.executable_path");

  requireFiniteNonNegative(record.execution.context_length, "execution.context_length");
  requireFiniteNonNegative(
    record.execution.max_generated_tokens,
    "execution.max_generated_tokens",
  );
  requireFiniteNonNegative(record.execution.temperature, "execution.temperature");
  requireFiniteNonNegative(
    record.execution.gpu_layers_requested,
    "execution.gpu_layers_requested",
  );
  requireFiniteNonNegative(
    record.execution.gpu_layers_offloaded,
    "execution.gpu_layers_offloaded",
  );
  if (!Array.isArray(record.execution.argv)) {
    throw new Error("execution.argv must be an array");
  }

  requireFiniteNonNegative(record.metrics.wall_time_ms, "metrics.wall_time_ms");
  requireNullableFiniteNonNegative(
    record.metrics.load_time_ms,
    "metrics.load_time_ms",
  );
  requireFiniteNonNegative(
    record.metrics.peak_process_ram_mib,
    "metrics.peak_process_ram_mib",
  );
  requireNullableFiniteNonNegative(
    record.metrics.vram_baseline_mib,
    "metrics.vram_baseline_mib",
  );
  requireNullableFiniteNonNegative(
    record.metrics.peak_vram_mib,
    "metrics.peak_vram_mib",
  );
  requireNullableFiniteNonNegative(
    record.metrics.vram_delta_mib,
    "metrics.vram_delta_mib",
  );
  requireFiniteNonNegative(
    record.metrics.prompt_tokens_per_sec,
    "metrics.prompt_tokens_per_sec",
  );
  requireFiniteNonNegative(
    record.metrics.generation_tokens_per_sec,
    "metrics.generation_tokens_per_sec",
  );

  if (record.execution.device === "CPU") {
    if (
      record.execution.device_id !== null ||
      record.execution.gpu_layers_offloaded !== 0
    ) {
      throw new Error("CPU execution cannot claim a GPU device or offloaded layers");
    }
  }

  if (record.execution.device === "CUDA") {
    requireNonBlank(record.execution.device_id ?? "", "execution.device_id");
    if (
      record.metrics.vram_baseline_mib === null ||
      record.metrics.peak_vram_mib === null ||
      record.metrics.vram_delta_mib === null
    ) {
      throw new Error("CUDA execution requires VRAM baseline, peak, and delta");
    }
  }

  if (record.cost.provider_api_cost_usd !== 0) {
    throw new Error("provider_api_cost_usd must be exactly 0 for local inference");
  }
  requireNullableFiniteNonNegative(
    record.cost.local_compute_cost_usd,
    "cost.local_compute_cost_usd",
  );

  requireNonBlank(record.evidence.stdout_path, "evidence.stdout_path");
  requireNonBlank(record.evidence.stderr_path, "evidence.stderr_path");
  requireNonBlank(record.evidence.metrics_path, "evidence.metrics_path");
}

export function serializeLocalInferenceMeasurementRecord(record: LocalInferenceMeasurementRecordV1): string {
  validateLocalInferenceMeasurementRecord(record);
  return JSON.stringify(record, null, 2) + "\n";
}

export function persistLocalInferenceMeasurementRecord(
  record: LocalInferenceMeasurementRecordV1,
  outputPath: string,
): void {
  validateLocalInferenceMeasurementRecord(record);
  const resolved = path.resolve(outputPath);
  fs.mkdirSync(path.dirname(resolved), { recursive: true });
  fs.writeFileSync(resolved, serializeLocalInferenceMeasurementRecord(record), {\n    encoding: "utf8",\n    flag: "wx",\n  });
}

/**
 * Backward-compatible names retained during reconciliation.
 *
 * Canonical generic execution telemetry:
 *   arkx.contracts.ExecutionRecord
 *
 * Specialized local-inference measurements:
 *   LocalInferenceMeasurementRecordV1
 *
 * These aliases preserve existing consumers; they do not establish a second
 * canonical generic ExecutionRecord boundary.
 */
export const EXECUTION_RECORD_SCHEMA_VERSION =
  LOCAL_INFERENCE_MEASUREMENT_SCHEMA_VERSION;

export const EXECUTION_RECORD_TYPE =
  LOCAL_INFERENCE_MEASUREMENT_RECORD_TYPE;

export type ExecutionRecordV1 =
  LocalInferenceMeasurementRecordV1;

export const validateExecutionRecord =
  validateLocalInferenceMeasurementRecord;

export const serializeExecutionRecord =
  serializeLocalInferenceMeasurementRecord;

export const persistExecutionRecord =
  persistLocalInferenceMeasurementRecord;

