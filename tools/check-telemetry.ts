import fs from "fs";
import path from "path";
import assert from "node:assert/strict";
import {
  LocalInferenceMeasurementRecordV1,
  persistLocalInferenceMeasurementRecord,
  validateLocalInferenceMeasurementRecord,
} from "../src/chassis/executionTelemetry";

const fixturePath = path.resolve("experiments/runtime-telemetry-fixture.json");
const fixture = JSON.parse(fs.readFileSync(fixturePath, "utf8")) as {
  records: LocalInferenceMeasurementRecordV1[];
};

assert.equal(fixture.records.length, 2);

for (const record of fixture.records) {
  validateLocalInferenceMeasurementRecord(record);
}

const cpu = fixture.records.find((record) => record.execution.device === "CPU");
const gpu = fixture.records.find((record) => record.execution.device === "CUDA");

assert.ok(cpu);
assert.ok(gpu);
assert.equal(cpu.termination.response_valid, true);
assert.equal(gpu.termination.response_valid, true);
assert.equal(gpu.execution.device_id, "CUDA0");
assert.equal(gpu.execution.gpu_layers_offloaded, 27);
assert.equal(gpu.metrics.vram_delta_mib, 906);
assert.equal(gpu.cost.provider_api_cost_usd, 0);

const tempPath = path.resolve(".telemetry-check", "record.json");
persistLocalInferenceMeasurementRecord(gpu, tempPath);
const roundTrip = JSON.parse(fs.readFileSync(tempPath, "utf8")) as LocalInferenceMeasurementRecordV1;
validateLocalInferenceMeasurementRecord(roundTrip);
assert.deepEqual(roundTrip, gpu);
fs.rmSync(path.dirname(tempPath), { recursive: true, force: true });

console.log("execution telemetry contract: PASS");

// Phase 3 controlled telemetry recapture.
const phase3FixturePath = path.resolve("experiments/runtime-telemetry-phase3-recapture.json");
const phase3Fixture = JSON.parse(fs.readFileSync(phase3FixturePath, "utf8")) as {
  records: LocalInferenceMeasurementRecordV1[];
};

assert.equal(phase3Fixture.records.length, 2);

for (const record of phase3Fixture.records) {
  validateLocalInferenceMeasurementRecord(record);

  for (const evidencePath of [
    record.evidence.stdout_path,
    record.evidence.stderr_path,
    record.evidence.metrics_path,
  ]) {
    assert.ok(
      fs.existsSync(path.resolve(evidencePath)),
      `raw telemetry evidence must exist: ${evidencePath}`,
    );
  }

  const stdout = fs.readFileSync(path.resolve(record.evidence.stdout_path), "utf8");
  const stderr = fs.readFileSync(path.resolve(record.evidence.stderr_path), "utf8");
  const raw = `${stdout}\n${stderr}`;
  const expectedResponse = record.termination.expected_response;

  assert.ok(expectedResponse);
  assert.ok(raw.includes(expectedResponse));
  assert.equal(record.termination.exit_code, 0);
  assert.ok(record.metrics.prompt_tokens_per_sec > 0);
  assert.ok(record.metrics.generation_tokens_per_sec > 0);
  assert.ok(record.metrics.peak_process_ram_mib > 0);
  assert.equal(record.cost.provider_api_cost_usd, 0);

  if (record.execution.device === "CUDA") {
    assert.notEqual(record.metrics.vram_baseline_mib, null);
    assert.notEqual(record.metrics.peak_vram_mib, null);
    assert.notEqual(record.metrics.vram_delta_mib, null);
    assert.ok((record.metrics.vram_delta_mib ?? 0) > 0);
  }
}

console.log("phase 3 controlled telemetry evidence: PASS");
