import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

import { executeVertical } from "../src/chassis/vertical";

function command(executable: string, args: string[], cwd: string): string {
  const result = spawnSync(executable, args, {
    cwd,
    encoding: "utf8",
    shell: false,
  });

  if (result.error) {
    throw result.error;
  }

  if (result.status !== 0) {
    throw new Error(
      [
        `command failed: ${executable} ${args.join(" ")}`,
        `status=${result.status}`,
        `stdout=${result.stdout ?? ""}`,
        `stderr=${result.stderr ?? ""}`,
      ].join("\n"),
    );
  }

  return (result.stdout ?? "").trim();
}

function initializeRepo(root: string): string {
  mkdirSync(root, { recursive: true });

  command("git", ["init"], root);
  command("git", ["config", "user.email", "r5@example.invalid"], root);
  command("git", ["config", "user.name", "CodePro R5"], root);

  writeFileSync(join(root, "target.txt"), "before\n", "utf8");

  command("git", ["add", "."], root);
  command("git", ["commit", "-m", "r5 fixture base"], root);

  return command("git", ["rev-parse", "HEAD"], root);
}

const python = process.env.CODEPRO_PYTHON?.trim();
const evidenceDir = process.env.CODEPRO_EVIDENCE_DIR?.trim();

if (!python) {
  throw new Error("CODEPRO_PYTHON missing");
}

if (!evidenceDir) {
  throw new Error("CODEPRO_EVIDENCE_DIR missing");
}

const root = mkdtempSync(join(tmpdir(), "codepro-r5-control-"));

try {
  const positiveRepo = join(root, "positive");
  const positiveRevision = initializeRepo(positiveRepo);

  const positive = executeVertical({
    workspace: positiveRepo,
    revision: positiveRevision,
    request_id: "r5-positive",
    task_id: "composed-real-vertical-positive",
    requester_ref: "user://r5-validator",
    authority_ref: "authority://r5-validator",
    acceptance_authority_ref: "acceptance://independent-pending",
    scope: ["target.txt"],
    candidate_files: ["target.txt"],
    affected_components: ["r5-fixture"],
    characterization_source_ref: "evidence://r5-positive-characterization",
    max_wall_time_seconds: 30,
    attempt_id: "attempt-positive",
    executor_argv: [
      python,
      "-c",
      "from pathlib import Path; Path('target.txt').write_text('after\\n', encoding='utf-8')",
    ],
    verifier_argv: [
      python,
      "-c",
      "from pathlib import Path; raise SystemExit(0 if Path('target.txt').read_text(encoding='utf-8') == 'after\\n' else 1)",
    ],
  });

  const positiveResult = join(positive.evidence_root, "result.json");

  if (positive.status !== "VERIFIED") {
    throw new Error(
      `positive status=${positive.status}; reason=${positive.reason}`,
    );
  }

  if (
    positive.changed_files.length !== 1 ||
    positive.changed_files[0] !== "target.txt"
  ) {
    throw new Error(
      `positive changed_files=${JSON.stringify(positive.changed_files)}`,
    );
  }

  if (!existsSync(positiveResult)) {
    throw new Error(`positive evidence missing: ${positiveResult}`);
  }

  const negativeRepo = join(root, "negative");
  const negativeRevision = initializeRepo(negativeRepo);

  const negative = executeVertical({
    workspace: negativeRepo,
    revision: negativeRevision,
    request_id: "r5-negative",
    task_id: "composed-real-vertical-negative",
    requester_ref: "user://r5-validator",
    authority_ref: "authority://r5-validator",
    acceptance_authority_ref: "acceptance://independent-pending",
    scope: ["target.txt"],
    candidate_files: ["target.txt"],
    affected_components: ["r5-fixture"],
    characterization_source_ref: "evidence://r5-negative-characterization",
    max_wall_time_seconds: 30,
    attempt_id: "attempt-negative",
    executor_argv: [
      python,
      "-c",
      "from pathlib import Path; Path('other.txt').write_text('OUTSIDE\\n', encoding='utf-8')",
    ],
    verifier_argv: [python, "-c", "raise SystemExit(0)"],
  });

  if (negative.status === "VERIFIED") {
    throw new Error("negative scope control was incorrectly VERIFIED");
  }

  if (
    negative.changed_files.length !== 1 ||
    negative.changed_files[0] !== "other.txt"
  ) {
    throw new Error(
      `negative changed_files=${JSON.stringify(negative.changed_files)}`,
    );
  }

  console.log(
    JSON.stringify(
      {
        positive: {
          status: positive.status,
          reason: positive.reason,
          changed_files: positive.changed_files,
          evidence_root: positive.evidence_root,
          result_json_exists: existsSync(positiveResult),
        },
        negative: {
          status: negative.status,
          reason: negative.reason,
          changed_files: negative.changed_files,
          evidence_root: negative.evidence_root,
        },
        provider_call: "NOT_EXECUTED",
        executor_promotion: "NOT_AUTHORIZED",
      },
      null,
      2,
    ),
  );
} finally {
  rmSync(root, { recursive: true, force: true });
}
