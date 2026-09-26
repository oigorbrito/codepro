#!/usr/bin/env python3
"""Qualify Gemini CLI as a real repository-edit executor using Google AI Pro auth.

The runner intentionally does not use a Gemini API key. It expects Gemini CLI
to be installed and already authenticated with the user's Google account.

Execution shape:
1. require Block-5 official verifier controls to be qualified;
2. resolve the frozen SWE-bench task metadata from the pinned task repo;
3. copy the exact /testbed workspace from the task image to a temporary host dir;
4. run Gemini CLI headlessly against that workspace;
5. capture stdout/stderr + structured JSON output + git patch;
6. grade the patch independently with SWE-bench 5.0.2.

A definitive verifier outcome (RESOLVED or TESTS_FAILED) qualifies executor
compatibility. It does not rank model quality or authorize product binding,
promotion, release, or fallback.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

DATASET = "princeton-nlp/SWE-bench_Verified"
SPLIT = "test"
DEFAULT_INSTANCE = "sympy__sympy-14711"

GEMINI_EXECUTOR = "gemini-cli"
GEMINI_MODEL = "gemini-3-pro-preview"
GEMINI_APPROVAL_MODE = "yolo"

VERIFIER_IMAGE = "codepro/swebench-verifier:5.0.2"
SWEBENCH_VERSION = "5.0.2"
TASK_REPO_COMMIT = "3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d"

QUALIFIED = "QUALIFIED_FOR_COMPARATIVE_RUN"
BLOCKED = "BLOCKED"
INCONCLUSIVE = "INCONCLUSIVE"

_TASK_HELPER = r"""
from __future__ import annotations
import json
import sys

from swebench.harness.utils import load_swebench_dataset
from swebench.task.repo import load_task_repo

dataset, split, instance_id, output_path = sys.argv[1:]
dataset_rows = load_swebench_dataset(dataset, split, [instance_id])
task_rows = load_task_repo("/opt/swe-bench-tasks", [instance_id])
if len(dataset_rows) != 1 or len(task_rows) != 1:
    raise RuntimeError("expected exactly one dataset and task-repo row")

dataset_instance = dict(dataset_rows[0])
task_instance = dict(task_rows[0])
for key in ("instance_id", "repo", "version", "base_commit"):
    if dataset_instance.get(key) != task_instance.get(key):
        raise RuntimeError(
            f"task identity mismatch for {key}: "
            f"dataset={dataset_instance.get(key)!r} task_repo={task_instance.get(key)!r}"
        )

payload = {
    "instance_id": instance_id,
    "repo": task_instance["repo"],
    "version": task_instance["version"],
    "base_commit": task_instance["base_commit"],
    "image": task_instance["image"],
    "problem_statement": dataset_instance["problem_statement"],
}
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
"""

_VERIFIER_HELPER = r"""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import sys

from swebench.harness.run_evaluation import main
from swebench.harness.utils import load_swebench_dataset
from swebench.task.repo import load_task_repo

dataset, split, instance_id, predictions_path, run_id, work_dir, normalized_report = sys.argv[1:]
os.environ["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
if shutil.which("docker") is None:
    raise RuntimeError("docker CLI unavailable inside verifier container")

work = Path(work_dir)
work.mkdir(parents=True, exist_ok=True)
os.chdir(work)

dataset_rows = load_swebench_dataset(dataset, split, [instance_id])
task_rows = load_task_repo("/opt/swe-bench-tasks", [instance_id])
if len(dataset_rows) != 1 or len(task_rows) != 1:
    raise RuntimeError("expected exactly one dataset and task-repo row")

dataset_instance = dict(dataset_rows[0])
task_instance = dict(task_rows[0])
for key in ("instance_id", "repo", "version", "base_commit"):
    if dataset_instance.get(key) != task_instance.get(key):
        raise RuntimeError(
            f"task identity mismatch for {key}: "
            f"dataset={dataset_instance.get(key)!r} task_repo={task_instance.get(key)!r}"
        )

harness_dataset = work / "harness-instance.json"
harness_dataset.write_text(
    json.dumps([task_instance], ensure_ascii=False) + "\n",
    encoding="utf-8",
)

report = main(
    dataset_name=str(harness_dataset),
    split=split,
    instance_ids=[instance_id],
    predictions_path=predictions_path,
    max_workers=1,
    open_file_limit=4096,
    run_id=run_id,
    timeout=1800,
    rewrite_reports=False,
    modal=False,
)

report_path = Path(report).resolve()
normalized = Path(normalized_report)
normalized.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(report_path, normalized)
print("CODEPRO_RESULT=" + json.dumps({"report": str(report_path), "normalized_report": str(normalized)}))
"""


def run(
    argv: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 3600,
) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    try:
        p = subprocess.run(
            argv,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
            check=False,
        )
        return {
            "argv": argv,
            "cwd": str(cwd) if cwd else None,
            "started_at": started,
            "returncode": p.returncode,
            "stdout": p.stdout,
            "stderr": p.stderr,
            "timeout": False,
            "error": None,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": argv,
            "cwd": str(cwd) if cwd else None,
            "started_at": started,
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timeout": True,
            "error": "TIMEOUT",
        }
    except OSError as exc:
        return {
            "argv": argv,
            "cwd": str(cwd) if cwd else None,
            "started_at": started,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "timeout": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def write_report(output_dir: Path, report: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "runner-summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def provider_free_gate_ok(path: Path) -> bool:
    try:
        data = load_json(path)
    except (OSError, json.JSONDecodeError):
        return False
    no_op = data.get("controls", {}).get("no_op", {})
    gold = data.get("controls", {}).get("gold_oracle", {})
    return (
        data.get("classification") == "MINI_V246_PROVIDER_FREE_RUNTIME_QUALIFIED"
        and no_op.get("execution") == "PASS"
        and no_op.get("verification") == "EXPECTED_FAIL"
        and no_op.get("cleanup") == "PASS"
        and gold.get("execution") == "PASS"
        and gold.get("verification") == "PASS"
        and gold.get("cleanup") == "PASS"
    )


def verifier_outcome(path: Path, instance_id: str) -> str:
    if not path.exists():
        return "INFRASTRUCTURE_ERROR"
    try:
        data = load_json(path)
    except (OSError, json.JSONDecodeError):
        return "INFRASTRUCTURE_ERROR"
    if instance_id in set(data.get("resolved_ids", ())):
        return "RESOLVED"
    if instance_id in set(data.get("unresolved_ids", ())):
        return "TESTS_FAILED"
    if instance_id in set(data.get("infra_failure_ids", ())):
        return "INFRASTRUCTURE_ERROR"
    if instance_id in set(data.get("ambiguous_failure_ids", ())):
        return "AMBIGUOUS"
    if instance_id in set(data.get("error_ids", ())):
        return "INFRASTRUCTURE_ERROR"
    return "AMBIGUOUS"


def _git(workspace: Path, *args: str, timeout: int = 120) -> dict[str, Any]:
    return run(["git", *args], cwd=workspace, timeout=timeout)


def _workspace_patch(workspace: Path) -> str | None:
    result = _git(workspace, "diff", "--binary", "HEAD", "--")
    if result["returncode"] != 0:
        return None
    patch = result["stdout"]
    return patch if patch.strip() else None


def _gemini_prompt(problem_statement: str) -> str:
    return (
        "You are the sole repository-edit executor for a controlled qualification run.\n"
        "Work only in the current git repository. Do not commit, push, change branches, "
        "or rewrite git history. Solve the issue below by editing the repository. "
        "Run relevant tests when useful. Do not create a final patch file; leave your "
        "working-tree changes in place for independent verification. Do not ask questions.\n\n"
        "<task>\n"
        + problem_statement.strip()
        + "\n</task>\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", default=DEFAULT_INSTANCE)
    parser.add_argument(
        "--runtime-evidence",
        type=Path,
        default=ROOT / "logs" / "architecture" / "mini-v246-verifier-controls-local" / "runner-summary.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "logs" / "qualification" / "gemini-cli-executor-local",
    )
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    parser.add_argument(
        "--authorize-account-usage",
        action="store_true",
        help="Required acknowledgement that the run consumes Gemini CLI quota from the signed-in account.",
    )
    args = parser.parse_args()

    output_dir = args.output_dir.expanduser().resolve()
    runtime_evidence = args.runtime_evidence.expanduser().resolve()

    report: dict[str, Any] = {
        "schema_version": 1,
        "block": "6",
        "classification": BLOCKED,
        "executor_promotion": "NOT_AUTHORIZED",
        "product_binding": "NOT_AUTHORIZED",
        "account_usage_authorized": bool(args.authorize_account_usage),
        "account_usage_attempted": False,
        "identity": {
            "executor": GEMINI_EXECUTOR,
            "model": GEMINI_MODEL,
            "authentication": "cached-google-account",
            "subscription_surface": "Google AI Pro / Gemini CLI",
            "approval_mode": GEMINI_APPROVAL_MODE,
            "dataset": DATASET,
            "split": SPLIT,
            "instance": args.instance,
            "verifier": "swebench.harness.run_evaluation",
            "verifier_version": SWEBENCH_VERSION,
            "task_repo_commit": TASK_REPO_COMMIT,
        },
        "budget": {
            "external_timeout_seconds": args.timeout_seconds,
            "max_executor_invocations": 1,
            "retries": 0,
        },
        "runtime_evidence": str(runtime_evidence),
        "execution": {"status": "NOT_EXECUTED"},
        "verification": {"status": "NOT_EXECUTED"},
        "trial": None,
        "steps": {},
    }
    write_report(output_dir, report)

    if not provider_free_gate_ok(runtime_evidence):
        report["reason"] = "BLOCK5_RUNTIME_EVIDENCE_NOT_QUALIFIED"
        write_report(output_dir, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    if not args.authorize_account_usage:
        report["reason"] = "ACCOUNT_USAGE_NOT_AUTHORIZED"
        write_report(output_dir, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    for tool in ("git", "docker", "gemini"):
        path = shutil.which(tool)
        report["steps"][f"tool_{tool}"] = {
            "path": path,
            "status": "PASS" if path else "FAIL",
        }
        if not path:
            report["reason"] = f"{tool.upper()}_UNAVAILABLE"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

    gemini_version = run(["gemini", "--version"], timeout=60)
    report["steps"]["gemini_version"] = gemini_version
    if gemini_version["returncode"] != 0:
        report["reason"] = "GEMINI_CLI_UNAVAILABLE"
        write_report(output_dir, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2
    report["identity"]["executor_version"] = gemini_version["stdout"].strip()

    verifier_identity = run(
        [
            "docker",
            "run",
            "--rm",
            VERIFIER_IMAGE,
            "sh",
            "-lc",
            (
                "set -eu; command -v docker; "
                "python -c \"import importlib.metadata as m; "
                "assert m.version('swebench') == '5.0.2'\"; "
                "test \"$(git -C /opt/swe-bench-tasks rev-parse HEAD)\" = "
                f"\"{TASK_REPO_COMMIT}\""
            ),
        ],
        timeout=120,
    )
    report["steps"]["verifier_identity"] = verifier_identity
    if verifier_identity["returncode"] != 0:
        report["reason"] = "VERIFIER_IMAGE_NOT_QUALIFIED"
        write_report(output_dir, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    output_dir.mkdir(parents=True, exist_ok=True)
    task_helper = output_dir / "task-metadata-helper.py"
    task_helper.write_text(_TASK_HELPER, encoding="utf-8", newline="\n")
    task_meta_path = output_dir / "task-metadata.json"
    evidence_mount = f"type=bind,source={output_dir},target=/evidence"

    task_meta_step = run(
        [
            "docker",
            "run",
            "--rm",
            "--mount",
            evidence_mount,
            VERIFIER_IMAGE,
            "python",
            "/evidence/task-metadata-helper.py",
            DATASET,
            SPLIT,
            args.instance,
            "/evidence/task-metadata.json",
        ],
        timeout=600,
    )
    report["steps"]["task_metadata"] = task_meta_step
    if task_meta_step["returncode"] != 0 or not task_meta_path.exists():
        report["reason"] = "TASK_METADATA_UNAVAILABLE"
        write_report(output_dir, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    task_meta = load_json(task_meta_path)
    report["task"] = {
        "instance_id": task_meta["instance_id"],
        "repo": task_meta["repo"],
        "version": task_meta["version"],
        "base_commit": task_meta["base_commit"],
        "image": task_meta["image"],
    }

    image_pull = run(["docker", "pull", task_meta["image"]], timeout=1800)
    report["steps"]["task_image_pull"] = image_pull
    if image_pull["returncode"] != 0:
        report["reason"] = "TASK_IMAGE_UNAVAILABLE"
        write_report(output_dir, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    with tempfile.TemporaryDirectory(prefix="codepro-gemini-cli-task-") as tmp:
        workspace = Path(tmp) / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)

        create = run(
            ["docker", "create", "--name", f"codepro-gemini-{datetime.now(timezone.utc).strftime('%H%M%S')}", task_meta["image"]],
            timeout=120,
        )
        report["steps"]["task_container_create"] = create
        if create["returncode"] != 0 or not create["stdout"].strip():
            report["reason"] = "TASK_WORKSPACE_CREATE_FAILED"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

        container_id = create["stdout"].strip()
        try:
            copy = run(["docker", "cp", f"{container_id}:/testbed/.", str(workspace)], timeout=600)
            report["steps"]["task_workspace_copy"] = copy
        finally:
            cleanup = run(["docker", "rm", "-f", container_id], timeout=120)
            report["steps"]["task_container_cleanup"] = cleanup

        if copy["returncode"] != 0 or cleanup["returncode"] != 0:
            report["reason"] = "TASK_WORKSPACE_COPY_FAILED"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

        head = _git(workspace, "rev-parse", "HEAD")
        clean = _git(workspace, "status", "--porcelain")
        ancestor = _git(workspace, "merge-base", "--is-ancestor", task_meta["base_commit"], "HEAD")
        report["steps"]["workspace_head"] = head
        report["steps"]["workspace_clean"] = clean
        report["steps"]["base_commit_ancestor"] = ancestor
        if (
            head["returncode"] != 0
            or clean["returncode"] != 0
            or clean["stdout"].strip()
            or ancestor["returncode"] != 0
        ):
            report["reason"] = "TASK_WORKSPACE_IDENTITY_INVALID"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

        prompt = _gemini_prompt(task_meta["problem_statement"])
        (output_dir / "executor-prompt.txt").write_text(prompt, encoding="utf-8")

        report["account_usage_attempted"] = True
        execution = run(
            [
                "gemini",
                "--model",
                GEMINI_MODEL,
                "--approval-mode",
                GEMINI_APPROVAL_MODE,
                "--output-format",
                "json",
                "--skip-trust",
                "--prompt",
                prompt,
            ],
            cwd=workspace,
            timeout=args.timeout_seconds,
        )
        report["steps"]["gemini_executor"] = execution

        response_json: dict[str, Any] | None = None
        if execution["stdout"].strip():
            try:
                parsed = json.loads(execution["stdout"])
                if isinstance(parsed, dict):
                    response_json = parsed
            except json.JSONDecodeError:
                response_json = None

        patch = _workspace_patch(workspace)
        changed = _git(workspace, "status", "--porcelain")
        changed_files = _git(workspace, "diff", "--name-only", "HEAD", "--")
        report["execution"] = {
            "status": (
                "COMPLETED"
                if execution["returncode"] == 0 and not execution["timeout"]
                else "BUDGET_EXHAUSTED"
                if execution["timeout"]
                else "EXECUTOR_FAILED"
            ),
            "returncode": execution["returncode"],
            "timeout": execution["timeout"],
            "structured_output": response_json is not None,
            "usage_stats_present": isinstance(response_json, dict) and isinstance(response_json.get("stats"), dict),
            "error_present": isinstance(response_json, dict) and response_json.get("error") is not None,
            "changed_files": [
                line.strip()
                for line in changed_files.get("stdout", "").splitlines()
                if line.strip()
            ],
            "patch_present": patch is not None,
            "patch_sha256": hashlib.sha256(patch.encode("utf-8")).hexdigest() if patch is not None else None,
        }

        if execution["returncode"] != 0 or execution["timeout"]:
            report["reason"] = "EXECUTOR_RUN_FAILED"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2
        if response_json is None or response_json.get("error") is not None:
            report["reason"] = "EXECUTOR_STRUCTURED_RESULT_INVALID"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2
        if patch is None or not changed.get("stdout", "").strip():
            report["reason"] = "EXECUTOR_PRODUCED_NO_PATCH"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

        patch_path = output_dir / "workspace.patch"
        patch_path.write_text(patch, encoding="utf-8", newline="\n")
        executor_result_path = output_dir / "gemini-result.json"
        executor_result_path.write_text(
            json.dumps(response_json, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    predictions_path = output_dir / "predictions.jsonl"
    predictions_path.write_text(
        json.dumps(
            {
                "instance_id": args.instance,
                "model_name_or_path": f"gemini-cli/{GEMINI_MODEL}",
                "model_patch": patch,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    verifier_helper = output_dir / "official-verifier-helper.py"
    verifier_helper.write_text(_VERIFIER_HELPER, encoding="utf-8", newline="\n")
    verifier_report = output_dir / "official-verifier-report.json"
    run_id = f"codepro-gemini-cli-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    verifier = run(
        [
            "docker",
            "run",
            "--rm",
            "--mount",
            "type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock",
            "--mount",
            evidence_mount,
            "--workdir",
            "/evidence",
            VERIFIER_IMAGE,
            "python",
            "/evidence/official-verifier-helper.py",
            DATASET,
            SPLIT,
            args.instance,
            "/evidence/predictions.jsonl",
            run_id,
            "/evidence/verifier-work",
            "/evidence/official-verifier-report.json",
        ],
        timeout=3600,
    )
    report["steps"]["official_verifier"] = verifier

    outcome = verifier_outcome(verifier_report, args.instance)
    cleanup_ok = (
        verifier["returncode"] == 0
        and "FileNotFoundError" not in (verifier.get("stderr") or "")
        and "Unstopped containers: 0" in (verifier.get("stdout") or "")
    )
    definitive = outcome in {"RESOLVED", "TESTS_FAILED"}
    report["verification"] = {
        "status": outcome,
        "definitive": definitive,
        "cleanup": "PASS" if cleanup_ok else "FAIL",
        "run_id": run_id,
        "report_path": str(verifier_report),
    }

    accepted = True if outcome == "RESOLVED" else False if outcome == "TESTS_FAILED" else None
    stats = response_json.get("stats") if isinstance(response_json, dict) else None
    report["trial"] = {
        "executor": {
            "name": GEMINI_EXECUTOR,
            "version": report["identity"].get("executor_version"),
            "integration_kind": "headless-cli",
            "configuration_digest": (
                f"model:{GEMINI_MODEL};approval:{GEMINI_APPROVAL_MODE};"
                f"prompt-sha256:{hashlib.sha256(_gemini_prompt(task_meta['problem_statement']).encode('utf-8')).hexdigest()}"
            ),
            "advertised_capabilities": ["repository-edit"],
        },
        "task": {
            "task_id": args.instance,
            "task_revision": TASK_REPO_COMMIT,
            "acceptance_definition": f"{SWEBENCH_VERSION}:official-verifier:{DATASET}:{SPLIT}",
        },
        "model": GEMINI_MODEL,
        "environment": {
            "repository_revision": report["steps"]["workspace_head"]["stdout"].strip(),
            "runtime": "host-gemini-cli+docker-task-image",
            "platform": "host",
            "toolchain": f"gemini-cli+official-swebench-{SWEBENCH_VERSION}",
            "environment_digest": f"task-image:{task_meta['image']}",
        },
        "budget": {
            "max_wall_time": str(args.timeout_seconds),
            "max_attempts": 1,
            "max_executor_invocations": 1,
        },
        "treatment": {
            "name": "gemini-cli-google-ai-pro",
            "enabled_mechanisms": [],
        },
        "replicate_id": "1",
        "outcome": "COMPLETED",
        "observation": {
            "accepted": accepted,
            "patch_verified": definitive,
            "false_pass": False if definitive else None,
            "attempts": 1,
            "retries": 0,
            "executor_invocations": 1,
            "usage_stats": stats,
            "external_evidence": [
                str(runtime_evidence),
                str(executor_result_path),
                str(patch_path),
                str(predictions_path),
                str(verifier_report),
            ],
        },
    }

    if not definitive or not cleanup_ok:
        report["classification"] = INCONCLUSIVE if verifier["returncode"] == 0 else BLOCKED
        report["reason"] = (
            "VERIFIER_OUTCOME_NOT_DEFINITIVE"
            if not definitive
            else "VERIFIER_CLEANUP_FAILED"
        )
        write_report(output_dir, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    report["classification"] = QUALIFIED
    report["reason"] = "COMPLETE_GEMINI_CLI_RUN_WITH_DEFINITIVE_OFFICIAL_VERIFICATION"
    write_report(output_dir, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
