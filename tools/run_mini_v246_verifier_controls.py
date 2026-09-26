#!/usr/bin/env python3
"""Run Block 5.1 official SWE-bench verifier controls without a model/provider.

The negative control uses a semantically inert repository-root text-file patch
instead of an empty patch because the official SWE-bench harness filters empty
predictions before verification. The positive control uses predictions_path=gold.

This runner does not call a model/provider, make a benchmark claim, accept an
executor, or authorize promotion.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import venv
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SWEBENCH_VERSION = "5.0.2"
DATASET = "princeton-nlp/SWE-bench_Verified"
SPLIT = "test"
DEFAULT_INSTANCE = "sympy__sympy-14711"

NEGATIVE_PATCH = """diff --git a/.codepro-verifier-negative-control.txt b/.codepro-verifier-negative-control.txt
new file mode 100644
--- /dev/null
+++ b/.codepro-verifier-negative-control.txt
@@ -0,0 +1 @@
+CodePro verifier negative control; intentionally unrelated to task behavior.
"""

_HELPER = r"""
import json
from pathlib import Path
import sys
from swebench.harness.run_evaluation import main

dataset, split, instance_id, predictions_path, run_id, report_dir = sys.argv[1:]
result = main(
    dataset_name=dataset,
    split=split,
    instance_ids=[instance_id],
    predictions_path=predictions_path,
    max_workers=1,
    open_file_limit=4096,
    run_id=run_id,
    timeout=1800,
    rewrite_reports=False,
    modal=False,
    report_dir=report_dir,
)
print("CODEPRO_RESULT=" + json.dumps({"report": str(result)}))
"""


def run(argv: list[str], *, cwd: Path | None = None, timeout: int = 3600) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    try:
        p = subprocess.run(
            argv,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
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


def venv_python(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def _extract_report_path(result: dict[str, Any]) -> Path | None:
    if result.get("returncode") != 0:
        return None
    for line in reversed(result.get("stdout", "").splitlines()):
        if line.startswith("CODEPRO_RESULT="):
            try:
                value = json.loads(line.split("=", 1)[1])
                return Path(value["report"]).expanduser().resolve()
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                return None
    return None


def _classify_report(path: Path | None, instance_id: str) -> dict[str, Any]:
    if path is None:
        return {"status": "INFRASTRUCTURE_ERROR", "report_path": None, "raw_outcome": None}
    if not path.exists():
        return {"status": "INFRASTRUCTURE_ERROR", "report_path": str(path), "raw_outcome": None}
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


def _write_report(output_dir: Path, report: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "runner-summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
        },
        "inputs": {"dataset": DATASET, "split": SPLIT, "instance": args.instance},
        "controls": {
            "no_op": {"execution": "NOT_EXECUTED", "verification": "NOT_EXECUTED"},
            "gold_oracle": {"execution": "NOT_EXECUTED", "verification": "NOT_EXECUTED"},
        },
        "steps": {},
    }
    _write_report(output_dir, report)

    for tool in ("docker",):
        path = shutil.which(tool)
        report["steps"][f"tool_{tool}"] = {"path": path, "status": "PASS" if path else "FAIL"}
        if not path:
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

    with tempfile.TemporaryDirectory(prefix="codepro-mini-v246-verifier-") as tmp:
        temp = Path(tmp)
        env_dir = temp / "venv"
        venv.EnvBuilder(with_pip=True, clear=True).create(env_dir)
        py = venv_python(env_dir)

        install = run(
            [
                str(py),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-input",
                f"swebench=={SWEBENCH_VERSION}",
            ],
            timeout=1800,
        )
        report["steps"]["install_verifier"] = install
        if install["returncode"] != 0:
            report["classification"] = "BLOCKED_VERIFIER_INSTALL"
            _write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

        identity = run(
            [
                str(py),
                "-c",
                "import importlib.metadata as m; print(m.version('swebench'))",
            ],
            timeout=60,
        )
        report["steps"]["verifier_identity"] = identity
        if identity["returncode"] != 0 or identity["stdout"].strip() != SWEBENCH_VERSION:
            report["classification"] = "BLOCKED_VERIFIER_IDENTITY"
            _write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

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
        )

        negative_run_id = "codepro-mini-v246-no-op-control"
        negative = run(
            [
                str(py),
                "-c",
                _HELPER,
                DATASET,
                SPLIT,
                args.instance,
                str(negative_prediction),
                negative_run_id,
                str(output_dir / "no-op"),
            ],
            cwd=ROOT,
            timeout=3600,
        )
        report["steps"]["no_op_verifier"] = negative
        negative_report = _extract_report_path(negative)
        negative_outcome = _classify_report(negative_report, args.instance)
        report["controls"]["no_op"] = {
            "execution": "PASS" if negative["returncode"] == 0 else "FAIL",
            "verification": "EXPECTED_FAIL" if negative_outcome["status"] == "TESTS_FAILED" else negative_outcome["status"],
            "run_id": negative_run_id,
            "semantic_no_op_patch": True,
            "reason": "non-empty inert patch forces official harness execution; empty patches are filtered",
            "outcome": negative_outcome,
        }
        if negative["returncode"] != 0 or negative_outcome["status"] != "TESTS_FAILED":
            report["classification"] = "BLOCKED_NEGATIVE_VERIFIER_CONTROL"
            _write_report(output_dir, report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 2

        gold_run_id = "codepro-mini-v246-gold-control"
        gold = run(
            [
                str(py),
                "-c",
                _HELPER,
                DATASET,
                SPLIT,
                args.instance,
                "gold",
                gold_run_id,
                str(output_dir / "gold"),
            ],
            cwd=ROOT,
            timeout=3600,
        )
        report["steps"]["gold_verifier"] = gold
        gold_report = _extract_report_path(gold)
        gold_outcome = _classify_report(gold_report, args.instance)
        report["controls"]["gold_oracle"] = {
            "execution": "PASS" if gold["returncode"] == 0 else "FAIL",
            "verification": "PASS" if gold_outcome["status"] == "RESOLVED" else gold_outcome["status"],
            "run_id": gold_run_id,
            "outcome": gold_outcome,
        }
        if gold["returncode"] != 0 or gold_outcome["status"] != "RESOLVED":
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
