#!/usr/bin/env python3
"""Run Block 5.1 official SWE-bench verifier controls without a model/provider.

The verifier is intentionally executed inside a Linux control container attached
to the already-qualified host Docker daemon. This avoids changing the frozen
Mini substrate while also avoiding host-Windows newline/multiprocessing effects
inside the official SWE-bench harness.

The negative control uses a semantically inert repository-root text-file patch
instead of an empty patch because the official harness filters empty predictions
before verification. The positive control uses predictions_path=gold.

No model/provider is called. No benchmark result, acceptance, or executor
promotion is authorized by this runner.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SWEBENCH_VERSION = "5.0.2"
DATASET = "princeton-nlp/SWE-bench_Verified"
SPLIT = "test"
DEFAULT_INSTANCE = "sympy__sympy-14711"
VERIFIER_BASE_IMAGE = "python:3.11-slim"
VERIFIER_IMAGE = "codepro/swebench-verifier:5.0.2"
TASK_REPO_URL = "https://github.com/SWE-bench/swe-bench-tasks.git"
TASK_REPO_COMMIT = "3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d"

NEGATIVE_PATCH = """diff --git a/.codepro-verifier-negative-control.txt b/.codepro-verifier-negative-control.txt
new file mode 100644
--- /dev/null
+++ b/.codepro-verifier-negative-control.txt
@@ -0,0 +1 @@
+CodePro verifier negative control; intentionally unrelated to task behavior.
"""

_LINUX_HELPER = r"""
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
work = Path(work_dir)
work.mkdir(parents=True, exist_ok=True)
os.chdir(work)

os.environ["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
docker_cli = shutil.which("docker")
if docker_cli is None:
    raise RuntimeError(f"docker CLI unavailable inside verifier container; PATH={os.environ['PATH']}")

rows = load_swebench_dataset(dataset, split, [instance_id])
if len(rows) != 1:
    raise RuntimeError(f"expected exactly one dataset row for {instance_id}, found {len(rows)}")
dataset_instance = dict(rows[0])

task_rows = load_task_repo("/opt/swe-bench-tasks", [instance_id])
if len(task_rows) != 1:
    raise RuntimeError(f"expected exactly one task-repo row for {instance_id}, found {len(task_rows)}")
task_instance = dict(task_rows[0])

for key in ("instance_id", "repo", "version", "base_commit"):
    if dataset_instance.get(key) != task_instance.get(key):
        raise RuntimeError(
            f"task-repo identity mismatch for {key}: "
            f"dataset={dataset_instance.get(key)!r} task_repo={task_instance.get(key)!r}"
        )

required = ("image", "eval_script", "log_parser", "eval_type", "FAIL_TO_PASS", "PASS_TO_PASS", "patch")
missing = [key for key in required if task_instance.get(key) is None]
if missing:
    raise RuntimeError("task-repo record missing required fields: " + ",".join(missing))

harness_dataset = work / "harness-instance.json"
harness_dataset.write_text(
    json.dumps([task_instance], ensure_ascii=False) + "\n",
    encoding="utf-8",
)

effective_predictions = predictions_path
if predictions_path == "gold":
    effective_predictions = "gold"

report = main(
    dataset_name=str(harness_dataset),
    split=split,
    instance_ids=[instance_id],
    predictions_path=effective_predictions,
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

_DOCKERFILE = f"""FROM {VERIFIER_BASE_IMAGE}
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends docker.io git ca-certificates \
 && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --disable-pip-version-check --no-input "swebench[datasets]=={SWEBENCH_VERSION}"
RUN python -c "import importlib.metadata as m; assert m.version('swebench') == '{SWEBENCH_VERSION}'; print(m.version('swebench'))"
RUN command -v docker && docker --version
RUN git init /opt/swe-bench-tasks \
 && git -C /opt/swe-bench-tasks remote add origin {TASK_REPO_URL} \
 && git -C /opt/swe-bench-tasks fetch --depth 1 origin {TASK_REPO_COMMIT} \
 && git -C /opt/swe-bench-tasks checkout --detach FETCH_HEAD \
 && test "$(git -C /opt/swe-bench-tasks rev-parse HEAD)" = "{TASK_REPO_COMMIT}" \
 && test -z "$(git -C /opt/swe-bench-tasks status --porcelain)"
"""


def run(argv: list[str], *, cwd: Path | None = None, timeout: int = 3600) -> dict[str, Any]:
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


def _classify_report(path: Path | None, instance_id: str) -> dict[str, Any]:
    if path is None or not path.exists():
        return {
            "status": "INFRASTRUCTURE_ERROR",
            "report_path": None if path is None else str(path),
            "raw_outcome": None,
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "status": "INFRASTRUCTURE_ERROR",
            "report_path": str(path),
            "raw_outcome": None,
            "error": f"{type(exc).__name__}: {exc}",
        }

    per_instance = data.get(instance_id)
    if isinstance(per_instance, dict) and "resolved" in per_instance:
        resolved = bool(per_instance["resolved"])
        return {
            "status": "RESOLVED" if resolved else "TESTS_FAILED",
            "report_path": str(path),
            "raw_outcome": resolved,
        }
    if instance_id in set(data.get("resolved_ids", ())):
        return {"status": "RESOLVED", "report_path": str(path), "raw_outcome": True}
    if instance_id in set(data.get("unresolved_ids", ())):
        return {"status": "TESTS_FAILED", "report_path": str(path), "raw_outcome": False}
    if instance_id in set(data.get("error_ids", ())):
        return {"status": "INFRASTRUCTURE_ERROR", "report_path": str(path), "raw_outcome": None}
    if instance_id in set(data.get("empty_patch_ids", ())):
        return {"status": "NOT_EXECUTED", "report_path": str(path), "raw_outcome": "EMPTY_PATCH_FILTERED"}
    return {"status": "AMBIGUOUS", "report_path": str(path), "raw_outcome": None}


def _verifier_image_identity_command() -> list[str]:
    return [
        "docker",
        "run",
        "--rm",
        VERIFIER_IMAGE,
        "sh",
        "-lc",
        (
            "set -eu; "
            "command -v docker; "
            "docker --version; "
            "python -c \"import importlib.metadata as m; "
            "assert m.version('swebench') == '" + SWEBENCH_VERSION + "'; "
            "print(m.version('swebench'))\"; "
            "test \"$(git -C /opt/swe-bench-tasks rev-parse HEAD)\" = "
            "\"" + TASK_REPO_COMMIT + "\"; "
            "test -z \"$(git -C /opt/swe-bench-tasks status --porcelain)\""
        ),
    ]


def _write_report(output_dir: Path, report: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "runner-summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _linux_control_command(
    output_dir: Path,
    *,
    instance: str,
    predictions_path: str,
    run_id: str,
    work_name: str,
    report_name: str,
) -> list[str]:
    evidence_mount = f"type=bind,source={output_dir},target=/evidence"
    socket_mount = "type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock"
    return [
        "docker",
        "run",
        "--rm",
        "--mount",
        socket_mount,
        "--mount",
        evidence_mount,
        "--workdir",
        "/evidence",
        VERIFIER_IMAGE,
        "python",
        "/evidence/linux-verifier-helper.py",
        DATASET,
        SPLIT,
        instance,
        predictions_path,
        run_id,
        f"/evidence/{work_name}",
        f"/evidence/{report_name}",
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", default=DEFAULT_INSTANCE)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "logs" / "architecture" / "mini-v246-verifier-controls-local",
    )
    args = parser.parse_args()
    output_dir = args.output_dir.expanduser().resolve()

    report: dict[str, Any] = {
        "schema_version": 1,
        "block": "5.1",
        "classification": "BLOCKED_NOT_EXECUTED",
        "provider_model": "NOT_EXECUTED",
        "benchmark": "NOT_EXECUTED",
        "executor_promotion": "NOT_AUTHORIZED",
        "verifier": {
            "authority": "swebench.harness.run_evaluation",
            "package": "swebench",
            "version": SWEBENCH_VERSION,
            "execution_platform": "linux-control-container",
            "image": VERIFIER_IMAGE,
            "task_repo": {
                "url": TASK_REPO_URL,
                "commit": TASK_REPO_COMMIT,
            },
        },
        "inputs": {"dataset": DATASET, "split": SPLIT, "instance": args.instance},
        "controls": {
            "no_op": {"execution": "NOT_EXECUTED", "verification": "NOT_EXECUTED"},
            "gold_oracle": {"execution": "NOT_EXECUTED", "verification": "NOT_EXECUTED"},
        },
        "steps": {},
    }
    _write_report(output_dir, report)

    docker_path = shutil.which("docker")
    report["steps"]["tool_docker"] = {
        "path": docker_path,
        "status": "PASS" if docker_path else "FAIL",
    }
    if not docker_path:
        report["classification"] = "BLOCKED_DOCKER_UNAVAILABLE"
        _write_report(output_dir, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    docker_info = run(["docker", "info", "--format", "{{json .}}"], timeout=60)
    report["steps"]["docker_info"] = docker_info
    if docker_info["returncode"] != 0:
        report["classification"] = "BLOCKED_DOCKER_DAEMON"
        _write_report(output_dir, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "linux-verifier-helper.py").write_text(_LINUX_HELPER, encoding="utf-8", newline="\n")
    negative_prediction = output_dir / "negative-control.jsonl"
    negative_prediction.write_text(
        json.dumps(
            {
                "instance_id": args.instance,
                "model_name_or_path": "codepro/provider-free-negative-control",
                "model_patch": NEGATIVE_PATCH,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    identity = run(_verifier_image_identity_command(), timeout=120)
    report["steps"]["existing_verifier_identity"] = identity

    if identity["returncode"] != 0:
        with tempfile.TemporaryDirectory(prefix="codepro-swebench-verifier-image-") as tmp:
            build_dir = Path(tmp)
            (build_dir / "Dockerfile").write_text(_DOCKERFILE, encoding="utf-8", newline="\n")
            build = run(
                ["docker", "build", "--pull", "-t", VERIFIER_IMAGE, str(build_dir)],
                timeout=2400,
            )
            report["steps"]["build_linux_verifier"] = build
            if build["returncode"] != 0:
                report["classification"] = "BLOCKED_VERIFIER_INSTALL"
                _write_report(output_dir, report)
                print(json.dumps(report, ensure_ascii=False, indent=2))
                return 2
        identity = run(_verifier_image_identity_command(), timeout=120)

    report["steps"]["verifier_identity"] = identity
    if identity["returncode"] != 0 or SWEBENCH_VERSION not in identity["stdout"]:
        report["classification"] = "BLOCKED_VERIFIER_IDENTITY"
        _write_report(output_dir, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    negative_run_id = f"codepro-mini-v246-no-op-{stamp}"
    negative = run(
        _linux_control_command(
            output_dir,
            instance=args.instance,
            predictions_path="/evidence/negative-control.jsonl",
            run_id=negative_run_id,
            work_name="no-op-work",
            report_name="no-op-official-report.json",
        ),
        cwd=ROOT,
        timeout=3600,
    )
    report["steps"]["no_op_verifier"] = negative
    negative_outcome = _classify_report(output_dir / "no-op-official-report.json", args.instance)
    report["controls"]["no_op"] = {
        "execution": "PASS" if negative["returncode"] == 0 else "FAIL",
        "verification": (
            "EXPECTED_FAIL"
            if negative_outcome["status"] == "TESTS_FAILED"
            else negative_outcome["status"]
        ),
        "run_id": negative_run_id,
        "semantic_no_op_patch": True,
        "reason": "non-empty inert patch forces official harness execution; empty patches are filtered",
        "outcome": negative_outcome,
    }
    negative_cleanup_error = (
        "FileNotFoundError" in (negative.get("stderr") or "")
        or "Unstopped containers: 0" not in (negative.get("stdout") or "")
        or "Unremoved images: 0" not in (negative.get("stdout") or "")
    )
    report["controls"]["no_op"]["cleanup"] = "FAIL" if negative_cleanup_error else "PASS"
    if negative["returncode"] != 0 or negative_outcome["status"] != "TESTS_FAILED" or negative_cleanup_error:
        report["classification"] = "BLOCKED_NEGATIVE_VERIFIER_CONTROL"
        _write_report(output_dir, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    gold_run_id = f"codepro-mini-v246-gold-{stamp}"
    gold = run(
        _linux_control_command(
            output_dir,
            instance=args.instance,
            predictions_path="gold",
            run_id=gold_run_id,
            work_name="gold-work",
            report_name="gold-official-report.json",
        ),
        cwd=ROOT,
        timeout=3600,
    )
    report["steps"]["gold_verifier"] = gold
    gold_outcome = _classify_report(output_dir / "gold-official-report.json", args.instance)
    report["controls"]["gold_oracle"] = {
        "execution": "PASS" if gold["returncode"] == 0 else "FAIL",
        "verification": "PASS" if gold_outcome["status"] == "RESOLVED" else gold_outcome["status"],
        "run_id": gold_run_id,
        "outcome": gold_outcome,
    }
    gold_cleanup_error = (
        "FileNotFoundError" in (gold.get("stderr") or "")
        or "Unstopped containers: 0" not in (gold.get("stdout") or "")
        or "Unremoved images: 0" not in (gold.get("stdout") or "")
    )
    report["controls"]["gold_oracle"]["cleanup"] = "FAIL" if gold_cleanup_error else "PASS"
    if gold["returncode"] != 0 or gold_outcome["status"] != "RESOLVED" or gold_cleanup_error:
        report["classification"] = "BLOCKED_GOLD_VERIFIER_CONTROL"
        _write_report(output_dir, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2

    report["classification"] = "MINI_V246_PROVIDER_FREE_RUNTIME_QUALIFIED"
    _write_report(output_dir, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
