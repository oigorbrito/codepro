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

assert.throws(
  () => persistLocalInferenceMeasurementRecord(cpu, tempPath),
  (error: unknown) =>
    error instanceof Error &&
    "code" in error &&
    (error as NodeJS.ErrnoException).code === "EEXIST",
);
const preserved = JSON.parse(
  fs.readFileSync(tempPath, "utf8"),
) as LocalInferenceMeasurementRecordV1;
assert.deepEqual(preserved, gpu);

fs.rmSync(path.dirname(tempPath), { recursive: true, force: true });

console.log("execution telemetry contract: PASS");
