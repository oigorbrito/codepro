#!/usr/bin/env python3
"""Provider-free SWE-bench task-environment qualification for pinned mini-SWE-agent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

PINNED_MINI_COMMIT = "a83fcae82d2a08f0ee0c688f9d137b3566c097f8"
PINNED_CONFIG_BLOB_SHA = "106decd160e72e5164e29d15d23da354c29c309d"
BUNDLED_CONFIG = Path("src/minisweagent/config/benchmarks/swebench.yaml")


def _run(argv: list[str], *, cwd: Path | None = None, timeout: int = 30) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            argv,
            cwd=str(cwd) if cwd is not None else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
            check=False,
        )
        return {
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "timeout": False,
            "error": None,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": argv,
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timeout": True,
            "error": "TIMEOUT",
        }
    except OSError as exc:
        return {
            "argv": argv,
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "timeout": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def classify_repo_state(*, ancestry_returncode: int, porcelain: str) -> str:
    if ancestry_returncode != 0:
        return "BASE_COMMIT_NOT_ANCESTOR"
    if porcelain.strip():
        return "WORKTREE_DIRTY"
    return "VALID_PREPARED_REPO_STATE"


def _mini_identity(mini_repo: Path) -> dict[str, Any]:
    head = _run(["git", "rev-parse", "HEAD"], cwd=mini_repo)
    status = _run(["git", "status", "--porcelain"], cwd=mini_repo)
    blob = _run(["git", "rev-parse", f"HEAD:{BUNDLED_CONFIG.as_posix()}"], cwd=mini_repo)
    actual_head = head["stdout"].strip() if head["returncode"] == 0 else None
    actual_blob = blob["stdout"].strip() if blob["returncode"] == 0 else None
    ok = (
        actual_head == PINNED_MINI_COMMIT
        and status["returncode"] == 0
        and not status["stdout"].strip()
        and actual_blob == PINNED_CONFIG_BLOB_SHA
    )
    return {
        "status": "PASS" if ok else "FAIL",
        "expected_commit": PINNED_MINI_COMMIT,
        "actual_commit": actual_head,
        "expected_config_blob": PINNED_CONFIG_BLOB_SHA,
        "actual_config_blob": actual_blob,
        "worktree_clean": status["returncode"] == 0 and not status["stdout"].strip(),
        "commands": {"head": head, "status": status, "config_blob": blob},
    }


def _import_pinned_mini(mini_repo: Path):
    src = str((mini_repo / "src").resolve())
    if src not in sys.path:
        sys.path.insert(0, src)

    from minisweagent.config import get_config_from_spec
    from minisweagent.run.benchmarks.swebench import (
        DATASET_MAPPING,
        get_sb_environment,
        get_swebench_docker_image_name,
    )

    return get_config_from_spec, DATASET_MAPPING, get_sb_environment, get_swebench_docker_image_name


def _load_instance(dataset_name: str, split: str, instance_id: str, revision: str | None):
    from datasets import load_dataset

    kwargs: dict[str, Any] = {"split": split}
    if revision:
        kwargs["revision"] = revision
    dataset = load_dataset(dataset_name, **kwargs)
    matches = [row for row in dataset if row["instance_id"] == instance_id]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one {instance_id!r}, found {len(matches)}")
    return dataset, matches[0]


def _execute(env: Any, command: str) -> dict[str, Any]:
    started = time.monotonic()
    result = env.execute({"command": command})
    return {"command": command, "duration_seconds": time.monotonic() - started, **result}


def _wait_for_cleanup(container_id: str | None, timeout_seconds: int = 70) -> dict[str, Any]:
    if not container_id:
        return {"status": "UNKNOWN", "reason": "NO_CONTAINER_ID"}
    deadline = time.monotonic() + timeout_seconds
    last: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        last = _run(["docker", "inspect", container_id])
        if last["returncode"] != 0:
            return {"status": "PASS", "container_id": container_id, "last_inspect": last}
        time.sleep(1)
    return {"status": "FAIL", "container_id": container_id, "last_inspect": last}


def _probe_once(get_sb_environment: Any, config: dict, instance: dict) -> dict[str, Any]:
    base_commit = instance["base_commit"]
    env = None
    report: dict[str, Any] = {"provider_called": False}
    try:
        env = get_sb_environment(config, instance)
        report["environment_type"] = f"{env.__class__.__module__}.{env.__class__.__name__}"
        report["container_id"] = getattr(env, "container_id", None)
        report["serialized_environment"] = env.serialize()

        pwd = _execute(env, "pwd")
        uname = _execute(env, "uname -s")
        head = _execute(env, "git -C /testbed rev-parse HEAD")
        status = _execute(env, "git -C /testbed status --porcelain=v1")
        ancestry = _execute(env, f"git -C /testbed merge-base --is-ancestor {base_commit} HEAD")
        ahead = _execute(env, f"git -C /testbed rev-list --count {base_commit}..HEAD")
        log = _execute(
            env,
            f"git -C /testbed log --format='%H%x09%P%x09%an%x09%s' {base_commit}..HEAD",
        )
        bash_env = _execute(env, 'printf "%s\\n" "$BASH_ENV"')

        repo_state = classify_repo_state(
            ancestry_returncode=ancestry["returncode"],
            porcelain=status["output"],
        )
        report["observations"] = {
            "pwd": pwd,
            "uname": uname,
            "head": head,
            "status": status,
            "ancestry": ancestry,
            "commits_ahead": ahead,
            "prepared_commits": log,
            "bash_env": bash_env,
        }
        report["repo_state"] = {
            "classification": repo_state,
            "base_commit": base_commit,
            "prepared_head": head["output"].strip(),
            "head_equals_base_commit": head["output"].strip() == base_commit,
            "base_commit_is_ancestor": ancestry["returncode"] == 0,
            "worktree_clean": not status["output"].strip(),
        }
        functional = (
            pwd["returncode"] == 0
            and pwd["output"].strip() == "/testbed"
            and uname["returncode"] == 0
            and uname["output"].strip() == "Linux"
            and repo_state == "VALID_PREPARED_REPO_STATE"
        )
        report["execution_status"] = "PASS" if functional else "FAIL"
    finally:
        if env is not None:
            env.cleanup()
            report["cleanup"] = _wait_for_cleanup(getattr(env, "container_id", None))
        else:
            report["cleanup"] = {"status": "NOT_EXECUTED"}

    report["status"] = (
        "PASS"
        if report.get("execution_status") == "PASS" and report["cleanup"]["status"] == "PASS"
        else "FAIL"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mini-repo", required=True, type=Path)
    parser.add_argument("--subset", default="verified")
    parser.add_argument("--split", default="test")
    parser.add_argument("--instance", required=True)
    parser.add_argument("--dataset-revision")
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.repeat < 1:
        parser.error("--repeat must be >= 1")

    mini_repo = args.mini_repo.expanduser().resolve()
    report: dict[str, Any] = {
        "schema_version": 1,
        "classification": "BLOCKED",
        "provider_called": False,
        "mini_identity": _mini_identity(mini_repo),
        "inputs": {
            "subset": args.subset,
            "split": args.split,
            "instance_id": args.instance,
            "dataset_revision": args.dataset_revision,
            "repeat": args.repeat,
        },
        "runs": [],
    }

    if report["mini_identity"]["status"] != "PASS":
        report["classification"] = "BLOCKED_REFERENCE_IDENTITY"
    else:
        get_config_from_spec, dataset_mapping, get_sb_environment, get_image = _import_pinned_mini(mini_repo)
        dataset_name = dataset_mapping.get(args.subset, args.subset)
        dataset, instance = _load_instance(dataset_name, args.split, args.instance, args.dataset_revision)
        config = get_config_from_spec(str(mini_repo / BUNDLED_CONFIG))
        image = get_image(instance)

        report["workload"] = {
            "dataset_name": dataset_name,
            "dataset_fingerprint": getattr(dataset, "_fingerprint", None),
            "instance_id": instance["instance_id"],
            "repo": instance.get("repo"),
            "base_commit": instance.get("base_commit"),
            "image": image,
            "image_name_field": instance.get("image_name"),
            "docker_image_field": instance.get("docker_image"),
        }

        for _ in range(args.repeat):
            report["runs"].append(_probe_once(get_sb_environment, config, instance))

        if all(run["status"] == "PASS" for run in report["runs"]):
            report["classification"] = "REFERENCE_PROVIDER_FREE_TASK_ENV_READY"
        elif any(
            run.get("repo_state", {}).get("classification") == "BASE_COMMIT_NOT_ANCESTOR"
            for run in report["runs"]
        ):
            report["classification"] = "TASK_IMAGE_PROVENANCE_MISMATCH_CONFIRMED"
        else:
            report["classification"] = "BLOCKED_MINI_SWEBENCH_ENVIRONMENT"

    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    sys.stdout.write(rendered)
    return 0 if report["classification"] == "REFERENCE_PROVIDER_FREE_TASK_ENV_READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
