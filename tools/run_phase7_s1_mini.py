#!/usr/bin/env python3
"""Run Phase 7 S1 mini-SWE-agent compatibility against the frozen local runtime."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from typing import Any
from urllib.request import urlopen


ROOT = Path(__file__).parents[1].resolve()
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from arkx.isolated_workspace import IsolatedGitWorkspace, capture_repository_state  # noqa: E402
from arkx.vertical import run_vertical  # noqa: E402


RUNTIME_ROOT = Path(r"D:\projetos\codepro-mini-runtime")
S1_ROOT = RUNTIME_ROOT / "phase7" / "S1-mini-swe-agent"
MINI_REPO = S1_ROOT / "upstream"
VENV = S1_ROOT / "venv"
INSTALL_MARKER = S1_ROOT / "installed.json"

MINI_URL = "https://github.com/SWE-agent/mini-swe-agent.git"
MINI_VERSION = "v2.4.6"
MINI_COMMIT = "a83fcae82d2a08f0ee0c688f9d137b3566c097f8"

MODEL_SHA256 = "E0406663965846AE22A403456EB826CCCE5F450840491F71952F18A7CB78E7D5"
MODEL_BYTES = 2244011552
MODEL_ALIAS = "codepro-phase7-granite42-3b"
PORT = 18089
BASE_URL = f"http://127.0.0.1:{PORT}/v1"

LLAMA_BUILD = 11205
LLAMA_COMMIT = "95887577ab5fead779581a7030a83c7752ff3234"


def run(
    argv: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 600,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
        check=False,
        timeout=timeout,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {argv!r}\n"
            f"stdout={completed.stdout[-4000:]}\n"
            f"stderr={completed.stderr[-4000:]}"
        )
    return completed


def write_json(path: Path, value: Any) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def find_model() -> Path:
    root = RUNTIME_ROOT / "models" / "phase4"
    for candidate in root.rglob("*.gguf"):
        if candidate.stat().st_size != MODEL_BYTES:
            continue
        if sha256(candidate) == MODEL_SHA256:
            return candidate.resolve()
    raise RuntimeError("frozen L3 Granite 4.2 3B artifact not found by SHA256")


def find_server() -> Path:
    root = RUNTIME_ROOT / "downloads" / "llama-b11205-bin-win-cuda-13.4-x64"
    matches = list(root.rglob("llama-server.exe"))
    if not matches:
        raise RuntimeError("frozen llama-server.exe not found")
    return matches[0].resolve()


def verify_port_available() -> None:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        listener.bind(("127.0.0.1", PORT))
    except OSError as exc:
        raise RuntimeError(f"explicit Phase 7 S1 port {PORT} unavailable") from exc
    finally:
        listener.close()


def ensure_upstream() -> dict[str, Any]:
    S1_ROOT.mkdir(parents=True, exist_ok=True)

    if not MINI_REPO.exists():
        run(["git", "clone", MINI_URL, str(MINI_REPO)], timeout=900)
    if not (MINI_REPO / ".git").exists():
        raise RuntimeError("S1 upstream path exists but is not a Git repository")

    status = run(
        ["git", "-C", str(MINI_REPO), "status", "--porcelain=v1"],
    ).stdout
    if status.strip():
        raise RuntimeError("S1 upstream checkout is dirty; refusing destructive reset")

    run(["git", "-C", str(MINI_REPO), "fetch", "--tags", "--prune", "origin"], timeout=900)
    run(["git", "-C", str(MINI_REPO), "checkout", "--detach", MINI_COMMIT])
    head = run(["git", "-C", str(MINI_REPO), "rev-parse", "HEAD"]).stdout.strip()
    if head != MINI_COMMIT:
        raise RuntimeError(f"S1 upstream identity mismatch: {head}")

    tag = run(
        ["git", "-C", str(MINI_REPO), "describe", "--tags", "--exact-match", "HEAD"],
        check=False,
    ).stdout.strip()
    if tag != MINI_VERSION:
        raise RuntimeError(f"S1 exact tag mismatch: {tag!r}")

    return {
        "repository": MINI_URL,
        "version": MINI_VERSION,
        "commit": head,
        "clean": True,
    }


def venv_python() -> Path:
    if os.name == "nt":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def ensure_install() -> dict[str, Any]:
    python = venv_python()
    marker_ok = False
    if INSTALL_MARKER.is_file() and python.is_file():
        try:
            marker = json.loads(INSTALL_MARKER.read_text(encoding="utf-8"))
            marker_ok = marker.get("commit") == MINI_COMMIT
        except json.JSONDecodeError:
            marker_ok = False

    if not marker_ok:
        if VENV.exists():
            shutil.rmtree(VENV)
        run([sys.executable, "-m", "venv", str(VENV)], timeout=300)
        python = venv_python()
        run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-input",
                str(MINI_REPO),
            ],
            timeout=1800,
        )
        INSTALL_MARKER.write_text(
            json.dumps(
                {
                    "repository": MINI_URL,
                    "version": MINI_VERSION,
                    "commit": MINI_COMMIT,
                    "python": str(python),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    version_probe = run(
        [
            str(python),
            "-c",
            "import minisweagent; print(minisweagent.__version__)",
        ]
    )
    observed_version = version_probe.stdout.strip()
    if observed_version != MINI_VERSION.removeprefix("v"):
        raise RuntimeError(
            f"installed mini-SWE-agent version mismatch: {observed_version!r}"
        )

    freeze = run([str(python), "-m", "pip", "freeze"], timeout=300).stdout.splitlines()
    return {
        "python": str(python.resolve()),
        "observed_version": observed_version,
        "pip_freeze": freeze,
    }


def wait_server(process: subprocess.Popen[Any], timeout_seconds: int = 120) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last_error = ""
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"llama-server exited before readiness: {process.returncode}")
        try:
            with urlopen(f"{BASE_URL}/health", timeout=2) as response:
                health = json.loads(response.read().decode("utf-8"))
            if health.get("status") == "ok":
                with urlopen(f"{BASE_URL}/models", timeout=2) as response:
                    models = json.loads(response.read().decode("utf-8"))
                ids = [
                    item.get("id")
                    for item in models.get("data", [])
                    if isinstance(item, dict)
                ]
                if MODEL_ALIAS not in ids:
                    raise RuntimeError(
                        f"explicit model alias missing from /models: {ids!r}"
                    )
                return {"health": health, "models": models}
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        time.sleep(0.5)
    raise RuntimeError(f"llama-server readiness timeout; last_error={last_error}")


def make_config(path: Path, workspace: Path) -> None:
    cwd = workspace.as_posix()
    content = f"""agent:
  step_limit: 8
  cost_limit: 0
  wall_time_limit_seconds: 120
  max_consecutive_format_errors: 2
environment:
  cwd: "{cwd}"
  timeout: 20
model:
  model_name: "openai/{MODEL_ALIAS}"
  cost_tracking: "ignore_errors"
  model_kwargs:
    custom_llm_provider: "openai"
    api_base: "{BASE_URL}"
    api_key: "local-llm"
    drop_params: true
    temperature: 1.0
    top_p: 0.95
    max_tokens: 512
"""
    path.write_text(content, encoding="utf-8", newline="\n")


def trajectory_observations(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {
            "present": False,
            "exit_status": None,
            "api_calls": None,
            "instance_cost": None,
            "commands": [],
            "prompt_tokens": None,
            "completion_tokens": None,
        }

    data = json.loads(path.read_text(encoding="utf-8"))
    info = data.get("info") or {}
    stats = info.get("model_stats") or {}
    commands: list[str] = []
    prompt_tokens = 0
    completion_tokens = 0
    token_usage_seen = False

    for message in data.get("messages", []):
        if not isinstance(message, dict):
            continue
        extra = message.get("extra")
        if not isinstance(extra, dict):
            continue
        actions = extra.get("actions")
        if isinstance(actions, list):
            for action in actions:
                if isinstance(action, dict) and isinstance(action.get("command"), str):
                    commands.append(action["command"])
        response = extra.get("response")
        if isinstance(response, dict):
            usage = response.get("usage")
            if isinstance(usage, dict):
                pt = usage.get("prompt_tokens")
                ct = usage.get("completion_tokens")
                if isinstance(pt, int):
                    prompt_tokens += pt
                    token_usage_seen = True
                if isinstance(ct, int):
                    completion_tokens += ct
                    token_usage_seen = True

    lowered = [command.lower() for command in commands]
    inspect_seen = any(
        "value.txt" in command
        and any(
            marker in command
            for marker in (
                "read_text",
                "get-content",
                "type ",
                "print(",
                "open(",
                "more ",
            )
        )
        for command in lowered
    )
    command_seen = bool(commands)

    return {
        "present": True,
        "exit_status": info.get("exit_status"),
        "submission": info.get("submission"),
        "api_calls": stats.get("api_calls"),
        "instance_cost": stats.get("instance_cost"),
        "commands": commands,
        "inspect_seen": inspect_seen,
        "command_seen": command_seen,
        "prompt_tokens": prompt_tokens if token_usage_seen else None,
        "completion_tokens": completion_tokens if token_usage_seen else None,
        "raw_info": info,
    }


def classify(
    vertical: dict[str, Any],
    trajectory: dict[str, Any],
    *,
    patch_ok: bool,
    verifier_ok: bool,
) -> str:
    exit_status = trajectory.get("exit_status")
    if exit_status == "RepeatedFormatError":
        return "BLOCKED_MODEL_TOOL_PROTOCOL"
    if vertical.get("status") == "TIMED_OUT":
        return "BLOCKED_TIMEOUT"
    if vertical.get("status") == "ENVIRONMENT_UNAVAILABLE":
        return "BLOCKED_ENVIRONMENT"
    if vertical.get("status") == "BLOCKED":
        return "BLOCKED_CODEPRO_GATE"

    compatible = all(
        (
            vertical.get("status") == "VERIFIED",
            trajectory.get("present") is True,
            isinstance(trajectory.get("api_calls"), int)
            and trajectory.get("api_calls") > 0,
            trajectory.get("inspect_seen") is True,
            trajectory.get("command_seen") is True,
            exit_status == "Submitted",
            patch_ok,
            verifier_ok,
        )
    )
    return "COMPATIBLE" if compatible else "INCOMPATIBLE"


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", required=True)
    args = parser.parse_args(argv)

    evidence = Path(args.evidence_dir).expanduser().resolve()
    if evidence.exists() and any(evidence.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty evidence directory: {evidence}")
    evidence.mkdir(parents=True, exist_ok=True)

    model = find_model()
    server = find_server()
    verify_port_available()
    upstream = ensure_upstream()
    installation = ensure_install()

    write_json(evidence / "upstream-identity.json", upstream)
    write_json(evidence / "installation.json", installation)

    server_stdout = evidence / "llama-server-stdout.txt"
    server_stderr = evidence / "llama-server-stderr.txt"
    server_argv = [
        str(server),
        "-m",
        str(model),
        "--device",
        "CUDA0",
        "-ngl",
        "99",
        "-c",
        "4096",
        "--host",
        "127.0.0.1",
        "--port",
        str(PORT),
        "--alias",
        MODEL_ALIAS,
    ]

    write_json(
        evidence / "runtime-binding.json",
        {
            "llama_cpp_build": LLAMA_BUILD,
            "llama_cpp_commit": LLAMA_COMMIT,
            "server": str(server),
            "server_argv": server_argv,
            "base_url": BASE_URL,
            "model_alias": MODEL_ALIAS,
            "model_artifact": str(model),
            "model_bytes": model.stat().st_size,
            "model_sha256": sha256(model),
            "fallback": "DISABLED",
        },
    )

    with server_stdout.open("w", encoding="utf-8", newline="\n") as out_handle, server_stderr.open(
        "w", encoding="utf-8", newline="\n"
    ) as err_handle:
        process = subprocess.Popen(
            server_argv,
            cwd=server.parent,
            stdout=out_handle,
            stderr=err_handle,
            text=True,
            shell=False,
        )
        isolated: IsolatedGitWorkspace | None = None
        old_env = {
            name: os.environ.get(name)
            for name in (
                "HOME",
                "APPDATA",
                "LOCALAPPDATA",
                "MSWEA_COST_TRACKING",
                "OPENAI_API_KEY",
            )
        }
        try:
            server_state = wait_server(process)
            write_json(evidence / "server-preflight.json", server_state)

            with tempfile.TemporaryDirectory(prefix="codepro-phase7-s1-", dir=S1_ROOT) as tmp:
                base = Path(tmp)
                source = base / "source"
                workspace_root = base / "workspaces"
                profile = base / "profile"
                source.mkdir()
                profile.mkdir()

                run(["git", "init"], cwd=source)
                run(["git", "config", "user.email", "phase7@example.invalid"], cwd=source)
                run(["git", "config", "user.name", "CodePro Phase 7"], cwd=source)
                (source / "value.txt").write_text("before\n", encoding="utf-8")
                run(["git", "add", "."], cwd=source)
                run(["git", "commit", "-m", "phase7-s1-base"], cwd=source)
                revision = run(["git", "rev-parse", "HEAD"], cwd=source).stdout.strip()

                isolated = IsolatedGitWorkspace.create(
                    source_repository=source,
                    revision=revision,
                    workspace_root=workspace_root,
                    workspace_id="s1-task",
                )

                config = evidence / "mini-local-runtime.yaml"
                trajectory_path = evidence / "mini-trajectory.json"
                make_config(config, isolated.workspace)

                for name in ("HOME", "APPDATA", "LOCALAPPDATA"):
                    os.environ[name] = str(profile)
                os.environ["MSWEA_COST_TRACKING"] = "ignore_errors"
                os.environ["OPENAI_API_KEY"] = "local-llm"

                task = (
                    "You are running on Windows. Work only in the current repository. "
                    "First inspect value.txt and confirm it contains the single line 'before'. "
                    "Then change that line to 'after'. Use Python commands for file inspection "
                    "and editing (do not use sed/cat/grep). Verify the resulting file content "
                    "with another Python command. Finally run exactly "
                    "'echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT' as a separate command."
                )

                python = Path(installation["python"])
                executor_argv = (
                    str(python),
                    "-m",
                    "minisweagent.run.mini",
                    "-y",
                    "--exit-immediately",
                    "-l",
                    "0",
                    "-t",
                    task,
                    "-c",
                    "mini.yaml",
                    "-c",
                    str(config),
                    "-o",
                    str(trajectory_path),
                )

                result = run_vertical(
                    workspace=isolated.workspace,
                    revision=revision,
                    request_id="phase7-s1-mini",
                    task_id="phase7-trivial-edit",
                    requester_ref="user://phase7-compatibility",
                    authority_ref="authority://phase7-compatibility",
                    acceptance_authority_ref="acceptance://phase7-independent-verifier",
                    scope=("value.txt",),
                    candidate_files=("value.txt",),
                    affected_components=("fixture",),
                    characterization_source_ref="evidence://phase7-s1-frozen-task",
                    executor_argv=executor_argv,
                    verifier_argv=(
                        sys.executable,
                        "-c",
                        "from pathlib import Path; "
                        "value=Path('value.txt').read_text(encoding='utf-8'); "
                        "print('VERIFIER_OK' if value == 'after\\n' else 'VERIFIER_BAD'); "
                        "raise SystemExit(0 if value == 'after\\n' else 9)",
                    ),
                    evidence_dir=evidence / "vertical",
                    max_wall_time_seconds=180,
                )

                vertical = result.to_dict()
                run_root = Path(result.evidence_root)
                patch_path = run_root / "workspace.patch"
                patch_text = (
                    patch_path.read_text(encoding="utf-8", errors="replace")
                    if patch_path.is_file()
                    else ""
                )
                patch_ok = (
                    "value.txt" in patch_text
                    and "-before" in patch_text
                    and "+after" in patch_text
                )
                verifier_summary_path = run_root / "verification-summary.json"
                verifier_summary = (
                    json.loads(verifier_summary_path.read_text(encoding="utf-8"))
                    if verifier_summary_path.is_file()
                    else {}
                )
                verifier_ok = verifier_summary.get("status") == "PASSED"
                trajectory = trajectory_observations(trajectory_path)

                final_state = isolated.capture_state().to_dict()
                source_state = capture_repository_state(source).to_dict()

                classification = classify(
                    vertical,
                    trajectory,
                    patch_ok=patch_ok,
                    verifier_ok=verifier_ok,
                )

                cleanup = isolated.remove()
                isolated = None

                summary = {
                    "schema_version": 1,
                    "phase": 7,
                    "candidate": "S1",
                    "scaffold": "mini-swe-agent",
                    "version": MINI_VERSION,
                    "commit": MINI_COMMIT,
                    "classification": classification,
                    "local_runtime": {
                        "base_url": BASE_URL,
                        "model_alias": MODEL_ALIAS,
                        "fallback": "DISABLED",
                    },
                    "vertical": vertical,
                    "trajectory": trajectory,
                    "gates": {
                        "exact_upstream_identity": True,
                        "installed_version": installation["observed_version"]
                        == MINI_VERSION.removeprefix("v"),
                        "local_runtime_ready": True,
                        "model_calls_observed": isinstance(
                            trajectory.get("api_calls"), int
                        )
                        and trajectory.get("api_calls") > 0,
                        "inspect_observed": trajectory.get("inspect_seen") is True,
                        "command_observed": trajectory.get("command_seen") is True,
                        "edit_observed": patch_ok,
                        "termination_observed": trajectory.get("exit_status")
                        == "Submitted",
                        "patch_captured": patch_ok,
                        "independent_verifier": verifier_ok,
                        "source_repository_unchanged": source_state.get("clean") is True,
                        "workspace_cleanup": cleanup.removed,
                    },
                    "repository_state": {
                        "initial_revision": revision,
                        "final": final_state,
                        "source": source_state,
                    },
                    "telemetry": {
                        "api_calls": trajectory.get("api_calls"),
                        "prompt_tokens": trajectory.get("prompt_tokens"),
                        "completion_tokens": trajectory.get("completion_tokens"),
                        "instance_cost": trajectory.get("instance_cost"),
                    },
                    "executor_promotion": "NOT_AUTHORIZED",
                    "selected_scaffold": False,
                    "next_candidate": "S2",
                }
                write_json(evidence / "s1-summary.json", summary)
                print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
                return 0
        finally:
            if isolated is not None:
                try:
                    isolated.remove()
                except Exception:
                    pass
            for name, value in old_env.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value
            if process.poll() is None:
                process.kill()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    pass


if __name__ == "__main__":
    raise SystemExit(main())
