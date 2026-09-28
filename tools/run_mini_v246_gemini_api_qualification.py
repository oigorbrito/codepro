#!/usr/bin/env python3
"""Run mini-SWE-agent v2.4.6 Phase-1 executor qualification.

This runner closes the compatibility/runtime questions from Issue #36 without
promoting the executor into CodePro's governed spine. It performs one real,
bounded upstream mini-SWE-agent run, captures trajectory + prediction, and
grades that prediction with the already-qualified official SWE-bench verifier.

A definitive verifier outcome (RESOLVED or TESTS_FAILED) is sufficient for
runtime comparability. Patch quality is deliberately not used as a proxy for
executor compatibility.

No fallback, executor switch, routing, retry policy mutation, or product
promotion is authorized here.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import venv
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

MINI_REPO_URL = "https://github.com/SWE-agent/mini-swe-agent.git"
MINI_VERSION = "v2.4.6"
MINI_SHA = "a83fcae82d2a08f0ee0c688f9d137b3566c097f8"
MINI_CONFIG = "src/minisweagent/config/benchmarks/swebench.yaml"
MINI_CONFIG_BLOB = "106decd160e72e5164e29d15d23da354c29c309d"

DATASET = "princeton-nlp/SWE-bench_Verified"
SPLIT = "test"
DEFAULT_INSTANCE = "sympy__sympy-14711"
MODEL = "gemini/gemini-2.5-flash"
PROVIDER_CREDENTIAL_ENV = "GEMINI_API_KEY"
COST_LIMIT_USD = 3
WORKERS = 1
ENVIRONMENT_CLASS = "docker"

VERIFIER_IMAGE = "codepro/swebench-verifier:5.0.2"
SWEBENCH_VERSION = "5.0.2"
TASK_REPO_COMMIT = "3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d"

QUALIFIED = "QUALIFIED_FOR_COMPARATIVE_RUN"
BLOCKED = "BLOCKED"
INCONCLUSIVE = "INCONCLUSIVE"

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
harness_dataset.write_text(json.dumps([task_instance], ensure_ascii=False) + "\n", encoding="utf-8")

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


def _load_verifier_builder():
    module_path = ROOT / "tools" / "run_mini_v246_verifier_controls.py"
    spec = importlib.util.spec_from_file_location("codepro_mini_verifier_controls", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load verifier control module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ensure_verifier_image(report: dict[str, Any]) -> bool:
    verifier = _load_verifier_builder()
    identity = run(verifier._verifier_image_identity_command(), timeout=120)
    report["steps"]["existing_verifier_identity"] = identity
    if identity["returncode"] == 0 and SWEBENCH_VERSION in identity["stdout"]:
        report["steps"]["verifier_identity"] = identity
        return True

    with tempfile.TemporaryDirectory(prefix="codepro-swebench-verifier-image-") as tmp:
        build_dir = Path(tmp)
        (build_dir / "Dockerfile").write_text(
            verifier._DOCKERFILE,
            encoding="utf-8",
            newline="\n",
        )
        build = run(
            ["docker", "build", "--pull", "-t", VERIFIER_IMAGE, str(build_dir)],
            timeout=2400,
        )
        report["steps"]["build_linux_verifier"] = build
        if build["returncode"] != 0:
            return False

    identity = run(verifier._verifier_image_identity_command(), timeout=120)
    report["steps"]["verifier_identity"] = identity
    return identity["returncode"] == 0 and SWEBENCH_VERSION in identity["stdout"]


def venv_python(path: Path) -> Path:
    return path / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def write_report(output_dir: Path, report: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "runner-summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def prediction_record(path: Path, instance_id: str) -> dict[str, Any] | None:
    try:
        data = load_json(path)
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(data, dict) and instance_id in data and isinstance(data[instance_id], dict):
        return data[instance_id]
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("instance_id") == instance_id:
                return item
    return None


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
        default=ROOT / "logs" / "qualification" / "mini-v246-executor-local",
    )
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    parser.add_argument(
        "--authorize-provider-call",
        action="store_true",
        help="Required acknowledgement that this run invokes the frozen Gemini API model.",
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
        "provider_call_authorized": bool(args.authorize_provider_call),
        "provider_call_attempted": False,
        "identity": {
            "executor": "mini-swe-agent",
            "executor_version": MINI_VERSION,
            "executor_commit": MINI_SHA,
            "integration_kind": "upstream-swebench-batch",
            "provider": "google-ai-studio-gemini-api",
            "config_path": MINI_CONFIG,
            "config_blob": MINI_CONFIG_BLOB,
            "model": MODEL,
            "environment_class": ENVIRONMENT_CLASS,
            "dataset": DATASET,
            "split": SPLIT,
            "instance": args.instance,
            "verifier": "swebench.harness.run_evaluation",
            "verifier_version": SWEBENCH_VERSION,
            "task_repo_commit": TASK_REPO_COMMIT,
        },
        "budget": {
            "cost_limit_usd": COST_LIMIT_USD,
            "workers": WORKERS,
            "external_timeout_seconds": args.timeout_seconds,
            "retry_policy": "UPSTREAM_FROZEN_CONFIG_ONLY",
        },
        "runtime_evidence": str(runtime_evidence),
        "execution": {"status": "NOT_EXECUTED"},
        "verification": {"status": "NOT_EXECUTED"},
        "trial": None,
        "steps": {},
    }
    write_report(output_dir, report)

    if not provider_free_gate_ok(runtime_evidence):
        report["classification"] = BLOCKED
        report["reason"] = "BLOCK5_RUNTIME_EVIDENCE_NOT_QUALIFIED"
        write_report(output_dir, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    if not args.authorize_provider_call:
        report["classification"] = BLOCKED
        report["reason"] = "PROVIDER_CALL_NOT_AUTHORIZED"
        write_report(output_dir, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    credential_present = bool(os.environ.get(PROVIDER_CREDENTIAL_ENV, "").strip())
    report["steps"]["provider_credential"] = {
        "environment_variable": PROVIDER_CREDENTIAL_ENV,
        "present": credential_present,
        "value_recorded": False,
    }
    if not credential_present:
        report["reason"] = "PROVIDER_CREDENTIAL_UNAVAILABLE"
        write_report(output_dir, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    for tool in ("git", "docker"):
        path = shutil.which(tool)
        report["steps"][f"tool_{tool}"] = {"path": path, "status": "PASS" if path else "FAIL"}
        if not path:
            report["reason"] = f"{tool.upper()}_UNAVAILABLE"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

    if not ensure_verifier_image(report):
        report["reason"] = "VERIFIER_IMAGE_NOT_QUALIFIED"
        write_report(output_dir, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    with tempfile.TemporaryDirectory(prefix="codepro-mini-v246-executor-") as tmp:
        temp = Path(tmp)
        mini_repo = temp / "mini-swe-agent"
        env_dir = temp / "venv"

        clone = run(["git", "clone", "--filter=blob:none", "--no-checkout", MINI_REPO_URL, str(mini_repo)], timeout=600)
        report["steps"]["clone_upstream"] = clone
        if clone["returncode"] != 0:
            report["reason"] = "UPSTREAM_FETCH_FAILED"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

        fetch = run(["git", "fetch", "--depth", "1", "origin", MINI_SHA], cwd=mini_repo, timeout=600)
        report["steps"]["fetch_exact_commit"] = fetch
        if fetch["returncode"] != 0:
            report["reason"] = "UPSTREAM_FETCH_FAILED"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

        checkout = run(["git", "checkout", "--detach", MINI_SHA], cwd=mini_repo, timeout=120)
        report["steps"]["checkout_exact_commit"] = checkout
        head = run(["git", "rev-parse", "HEAD"], cwd=mini_repo, timeout=30)
        blob = run(["git", "rev-parse", f"HEAD:{MINI_CONFIG}"], cwd=mini_repo, timeout=30)
        clean = run(["git", "status", "--porcelain"], cwd=mini_repo, timeout=30)
        report["steps"]["mini_head"] = head
        report["steps"]["mini_config_blob"] = blob
        report["steps"]["mini_worktree"] = clean
        if (
            checkout["returncode"] != 0
            or head.get("stdout", "").strip() != MINI_SHA
            or blob.get("stdout", "").strip() != MINI_CONFIG_BLOB
            or clean.get("stdout", "").strip()
        ):
            report["reason"] = "REFERENCE_IDENTITY_MISMATCH"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

        venv.EnvBuilder(with_pip=True, clear=True).create(env_dir)
        py = venv_python(env_dir)
        install = run(
            [str(py), "-m", "pip", "install", "--disable-pip-version-check", "--no-input", str(mini_repo)],
            timeout=1200,
        )
        report["steps"]["install_pinned_mini"] = install
        if install["returncode"] == 0:
            dependency_versions = run(
                [
                    str(py),
                    "-c",
                    (
                        "import importlib.metadata as m, json; "
                        "print(json.dumps({'mini-swe-agent': m.version('mini-swe-agent'), "
                        "'litellm': m.version('litellm')}))"
                    ),
                ],
                timeout=60,
            )
            report["steps"]["model_backend_versions"] = dependency_versions
            if dependency_versions["returncode"] == 0:
                try:
                    report["identity"]["model_backend_versions"] = json.loads(
                        dependency_versions["stdout"].strip()
                    )
                except json.JSONDecodeError:
                    pass
        if install["returncode"] != 0:
            report["reason"] = "MINI_INSTALL_FAILED"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

        mini_output = output_dir / "mini-run"
        mini_output.mkdir(parents=True, exist_ok=True)
        report["provider_call_attempted"] = True
        execution = run(
            [
                str(py),
                "-m",
                "minisweagent.run.benchmarks.swebench",
                "--subset",
                "verified",
                "--split",
                SPLIT,
                "--filter",
                f"^{re.escape(args.instance)}$",
                "--output",
                str(mini_output),
                "--workers",
                str(WORKERS),
                "--model",
                MODEL,
                "--environment-class",
                ENVIRONMENT_CLASS,
                "--redo-existing",
            ],
            timeout=args.timeout_seconds,
        )
        report["steps"]["mini_executor"] = execution

        preds_path = mini_output / "preds.json"
        traj_path = mini_output / args.instance / f"{args.instance}.traj.json"
        pred = prediction_record(preds_path, args.instance)
        patch = None if pred is None else pred.get("model_patch")
        trajectory_present = traj_path.exists()
        patch_present = isinstance(patch, str) and bool(patch.strip())
        report["execution"] = {
            "status": "COMPLETED" if execution["returncode"] == 0 and not execution["timeout"] else (
                "BUDGET_EXHAUSTED" if execution["timeout"] else "EXECUTOR_FAILED"
            ),
            "returncode": execution["returncode"],
            "timeout": execution["timeout"],
            "trajectory_present": trajectory_present,
            "trajectory_path": str(traj_path),
            "prediction_path": str(preds_path),
            "patch_present": patch_present,
            "patch_sha256": hashlib.sha256(patch.encode("utf-8")).hexdigest() if patch_present else None,
        }

        if execution["returncode"] != 0 or execution["timeout"] or not trajectory_present or not patch_present:
            report["classification"] = BLOCKED
            report["reason"] = "EXECUTOR_RUN_NOT_OBSERVABLE"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

        verifier_helper = output_dir / "official-verifier-helper.py"
        verifier_helper.write_text(_VERIFIER_HELPER, encoding="utf-8", newline="\n")
        verifier_report = output_dir / "official-verifier-report.json"
        run_id = f"codepro-mini-v246-executor-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        evidence_mount = f"type=bind,source={output_dir},target=/evidence"
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
                "/evidence/mini-run/preds.json",
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
        report["trial"] = {
            "executor": {
                "name": "mini-swe-agent",
                "version": MINI_VERSION,
                "integration_kind": "upstream-swebench-batch",
                "configuration_digest": f"gitblob:{MINI_CONFIG_BLOB}",
                "advertised_capabilities": ["repository-edit"],
            },
            "task": {
                "task_id": args.instance,
                "task_revision": TASK_REPO_COMMIT,
                "acceptance_definition": f"{SWEBENCH_VERSION}:official-verifier:{DATASET}:{SPLIT}",
            },
            "model": MODEL,
            "environment": {
                "repository_revision": MINI_SHA,
                "runtime": "docker",
                "platform": "linux/x86_64",
                "toolchain": f"mini-swe-agent-{MINI_VERSION}+swebench-{SWEBENCH_VERSION}",
                "environment_digest": f"mini-config-gitblob:{MINI_CONFIG_BLOB}",
            },
            "budget": {
                "max_cost": str(COST_LIMIT_USD),
                "max_wall_time": str(args.timeout_seconds),
                "max_attempts": 1,
                "max_executor_invocations": 1,
            },
            "treatment": {
                "name": "mini-v246-gemini-api",
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
                "external_evidence": [
                    str(runtime_evidence),
                    str(traj_path),
                    str(preds_path),
                    str(verifier_report),
                ],
            },
        }

        if not definitive or not cleanup_ok:
            report["classification"] = INCONCLUSIVE if verifier["returncode"] == 0 else BLOCKED
            report["reason"] = "VERIFIER_OUTCOME_NOT_DEFINITIVE" if not definitive else "VERIFIER_CLEANUP_FAILED"
            write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

    report["classification"] = QUALIFIED
    report["reason"] = "COMPLETE_OBSERVABLE_RUN_WITH_DEFINITIVE_OFFICIAL_VERIFICATION"
    write_report(output_dir, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
