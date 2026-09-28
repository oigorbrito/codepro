#!/usr/bin/env python3
"""Run Phase 7 S3 AutoCodeRover compatibility on the Windows-native baseline."""

from __future__ import annotations

import argparse
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
S3_ROOT = RUNTIME_ROOT / "phase7" / "S3-AutoCodeRover"
UPSTREAM = S3_ROOT / "upstream"
VENV = S3_ROOT / "venv"
INSTALL_MARKER = S3_ROOT / "installed.json"

UPSTREAM_URL = "https://github.com/AutoCodeRoverSG/auto-code-rover.git"
VERSION = "v1.1.0"
COMMIT = "1aafff1be4549fff4db9d61bf54bfa8b0669ea57"

MODEL_SHA256 = "E0406663965846AE22A403456EB826CCCE5F450840491F71952F18A7CB78E7D5"
MODEL_BYTES = 2244011552
MODEL_ALIAS = "codepro-phase7-granite42-3b"
PORT = 18091
BASE_URL = f"http://127.0.0.1:{PORT}/v1"
LLAMA_BUILD = 11205
LLAMA_COMMIT = "95887577ab5fead779581a7030a83c7752ff3234"


def run(argv: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None, timeout: int = 900, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        argv, cwd=cwd, env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", shell=False, check=False, timeout=timeout
    )
    if check and completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {argv!r}\n"
            f"stdout={completed.stdout[-4000:]}\nstderr={completed.stderr[-4000:]}"
        )
    return completed


def write_json(path: Path, value: Any) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def summary_base() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "phase": 7,
        "candidate": "S3",
        "scaffold": "AutoCodeRover",
        "version": VERSION,
        "commit": COMMIT,
        "classification": "BLOCKED_UNCLASSIFIED",
        "local_runtime": {"base_url": BASE_URL, "model_alias": MODEL_ALIAS, "fallback": "DISABLED"},
        "native_contract": "PlainTask -> ProjectApiManager structural search tools -> upstream OpenaiModel tool calls -> write_patch -> extracted patch -> CodePro verifier",
        "gates": {},
        "telemetry": {},
        "vertical": None,
        "adapter": None,
        "selected_scaffold": False,
        "executor_promotion": "NOT_AUTHORIZED",
        "next_candidate": "S4",
    }


def block(evidence: Path, summary: dict[str, Any], classification: str, stage: str, detail: Any) -> int:
    summary["classification"] = classification
    summary["blocker"] = {"stage": stage, "detail": detail}
    write_json(evidence / "s3-summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def ensure_upstream(evidence: Path, summary: dict[str, Any]) -> bool:
    S3_ROOT.mkdir(parents=True, exist_ok=True)
    if not UPSTREAM.exists():
        clone = run(["git", "clone", UPSTREAM_URL, str(UPSTREAM)], timeout=1200, check=False)
        write_json(evidence / "clone.json", {"returncode": clone.returncode, "stdout": clone.stdout, "stderr": clone.stderr})
        if clone.returncode != 0:
            summary["blocker"] = {"stage": "clone", "detail": clone.stderr[-4000:]}
            return False
    status = run(["git", "-C", str(UPSTREAM), "status", "--porcelain=v1"], check=False)
    if status.returncode != 0 or status.stdout.strip():
        summary["blocker"] = {"stage": "upstream_cleanliness", "detail": status.stdout + status.stderr}
        return False
    fetch = run(["git", "-C", str(UPSTREAM), "fetch", "--tags", "--prune", "origin"], timeout=1200, check=False)
    if fetch.returncode != 0:
        summary["blocker"] = {"stage": "fetch", "detail": fetch.stderr[-4000:]}
        return False
    checkout = run(["git", "-C", str(UPSTREAM), "checkout", "--detach", COMMIT], check=False)
    if checkout.returncode != 0:
        summary["blocker"] = {"stage": "checkout", "detail": checkout.stderr[-4000:]}
        return False
    head = run(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"]).stdout.strip()
    tag = run(["git", "-C", str(UPSTREAM), "describe", "--tags", "--exact-match", "HEAD"], check=False).stdout.strip()
    write_json(evidence / "upstream-identity.json", {"repository": UPSTREAM_URL, "version": VERSION, "commit": head, "tag": tag, "clean": True})
    summary["gates"]["exact_upstream_identity"] = head == COMMIT and tag == VERSION
    return summary["gates"]["exact_upstream_identity"]


def find_python311(summary: dict[str, Any]) -> Path | None:
    launcher = shutil.which("py")
    if not launcher:
        summary["blocker"] = {"stage": "python_runtime", "detail": "Windows py launcher not found"}
        return None
    probe = run([launcher, "-3.11", "-c", "import sys; print(sys.executable)"], check=False)
    if probe.returncode != 0:
        summary["blocker"] = {"stage": "python_runtime", "detail": probe.stderr[-4000:] or probe.stdout[-4000:]}
        return None
    summary["gates"]["python_3_11"] = True
    return Path(probe.stdout.strip())


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def ensure_exact_install(evidence: Path, base_python: Path, summary: dict[str, Any]) -> Path | None:
    python = venv_python()
    marker_ok = False
    if INSTALL_MARKER.is_file() and python.is_file():
        try:
            marker = json.loads(INSTALL_MARKER.read_text(encoding="utf-8"))
            marker_ok = marker.get("commit") == COMMIT and marker.get("requirements_mode") == "EXACT_UPSTREAM"
        except json.JSONDecodeError:
            marker_ok = False
    if not marker_ok:
        if VENV.exists():
            shutil.rmtree(VENV)
        created = run([str(base_python), "-m", "venv", str(VENV)], timeout=600, check=False)
        if created.returncode != 0:
            summary["blocker"] = {"stage": "venv", "detail": created.stderr[-4000:]}
            return None
        python = venv_python()
        installed = run(
            [str(python), "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "-r", str(UPSTREAM / "requirements.txt")],
            timeout=5400,
            check=False,
        )
        (evidence / "install-stdout.txt").write_text(installed.stdout, encoding="utf-8", newline="\n")
        (evidence / "install-stderr.txt").write_text(installed.stderr, encoding="utf-8", newline="\n")
        if installed.returncode != 0:
            summary["blocker"] = {
                "stage": "exact_upstream_requirements",
                "returncode": installed.returncode,
                "stderr_tail": installed.stderr[-6000:],
                "stdout_tail": installed.stdout[-3000:],
            }
            summary["gates"]["exact_upstream_requirements"] = False
            return None
        INSTALL_MARKER.write_text(
            json.dumps({"repository": UPSTREAM_URL, "version": VERSION, "commit": COMMIT, "python": str(python), "requirements_mode": "EXACT_UPSTREAM"}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    freeze = run([str(python), "-m", "pip", "freeze"], timeout=600, check=False)
    write_json(evidence / "installation.json", {"python": str(python.resolve()), "requirements_mode": "EXACT_UPSTREAM", "pip_freeze": freeze.stdout.splitlines()})
    summary["gates"]["exact_upstream_requirements"] = freeze.returncode == 0
    return python if summary["gates"]["exact_upstream_requirements"] else None


def find_model() -> Path:
    root = RUNTIME_ROOT / "models" / "phase4"
    for candidate in root.rglob("*.gguf"):
        if candidate.stat().st_size == MODEL_BYTES and sha256(candidate) == MODEL_SHA256:
            return candidate.resolve()
    raise RuntimeError("frozen L3 artifact not found by SHA256")


def find_server() -> Path:
    root = RUNTIME_ROOT / "downloads" / "llama-b11205-bin-win-cuda-13.4-x64"
    matches = list(root.rglob("llama-server.exe"))
    if not matches:
        raise RuntimeError("frozen llama-server.exe not found")
    return matches[0].resolve()


def verify_port() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", PORT))
    except OSError as exc:
        raise RuntimeError(f"explicit S3 port {PORT} unavailable") from exc
    finally:
        sock.close()


def wait_server(process: subprocess.Popen[Any], timeout_seconds: int = 120) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last = ""
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"llama-server exited early: {process.returncode}")
        try:
            with urlopen(f"{BASE_URL}/health", timeout=2) as response:
                health = json.loads(response.read().decode("utf-8"))
            with urlopen(f"{BASE_URL}/models", timeout=2) as response:
                models = json.loads(response.read().decode("utf-8"))
            ids = [item.get("id") for item in models.get("data", []) if isinstance(item, dict)]
            if health.get("status") == "ok" and MODEL_ALIAS in ids:
                return {"health": health, "models": models}
        except Exception as exc:
            last = f"{type(exc).__name__}: {exc}"
        time.sleep(0.5)
    raise RuntimeError(f"server readiness timeout: {last}")


def classify(vertical: dict[str, Any], adapter: dict[str, Any], verifier_ok: bool, patch_ok: bool) -> str:
    error = adapter.get("error")
    stats = adapter.get("stats") if isinstance(adapter.get("stats"), dict) else {}
    model_calls_observed = isinstance(stats.get("total_input_tokens"), int) and stats.get("total_input_tokens") > 0
    if error and not model_calls_observed:
        return "BLOCKED_SCAFFOLD_STARTUP"
    if vertical.get("status") == "TIMED_OUT":
        return "BLOCKED_TIMEOUT"
    if model_calls_observed and not adapter.get("patch_applied"):
        return "BLOCKED_MODEL_TOOL_OR_PATCH_FORMAT"
    if vertical.get("status") == "VERIFIED" and adapter.get("patch_applied") and verifier_ok and patch_ok:
        return "COMPATIBLE"
    if vertical.get("status") == "ENVIRONMENT_UNAVAILABLE":
        return "BLOCKED_ENVIRONMENT"
    return "INCOMPATIBLE"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", required=True)
    args = parser.parse_args(argv)
    evidence = Path(args.evidence_dir).expanduser().resolve()
    if evidence.exists() and any(evidence.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty evidence directory: {evidence}")
    evidence.mkdir(parents=True, exist_ok=True)
    summary = summary_base()

    try:
        if not ensure_upstream(evidence, summary):
            return block(evidence, summary, "BLOCKED_UPSTREAM_IDENTITY", "upstream", summary.get("blocker"))
        py311 = find_python311(summary)
        if py311 is None:
            return block(evidence, summary, "BLOCKED_PYTHON_RUNTIME", "python_runtime", summary.get("blocker"))
        acr_python = ensure_exact_install(evidence, py311, summary)
        if acr_python is None:
            return block(evidence, summary, "BLOCKED_INSTALLATION_WINDOWS_NATIVE", "installation", summary.get("blocker"))

        model = find_model()
        server = find_server()
        verify_port()
        server_argv = [str(server), "-m", str(model), "--device", "CUDA0", "-ngl", "99", "-c", "4096", "--host", "127.0.0.1", "--port", str(PORT), "--alias", MODEL_ALIAS]
        write_json(evidence / "runtime-binding.json", {"llama_cpp_build": LLAMA_BUILD, "llama_cpp_commit": LLAMA_COMMIT, "server": str(server), "server_argv": server_argv, "base_url": BASE_URL, "model_alias": MODEL_ALIAS, "model_artifact": str(model), "model_bytes": model.stat().st_size, "model_sha256": sha256(model), "fallback": "DISABLED"})

        with (evidence / "llama-server-stdout.txt").open("w", encoding="utf-8", newline="\n") as out_handle, (evidence / "llama-server-stderr.txt").open("w", encoding="utf-8", newline="\n") as err_handle:
            process = subprocess.Popen(server_argv, cwd=server.parent, stdout=out_handle, stderr=err_handle, text=True, shell=False)
            isolated: IsolatedGitWorkspace | None = None
            try:
                preflight = wait_server(process)
                summary["gates"]["local_runtime_ready"] = True
                write_json(evidence / "server-preflight.json", preflight)

                with tempfile.TemporaryDirectory(prefix="codepro-phase7-s3-", dir=S3_ROOT) as tmp:
                    base = Path(tmp)
                    source = base / "source"
                    workspaces = base / "workspaces"
                    source.mkdir()
                    run(["git", "init"], cwd=source)
                    run(["git", "config", "user.email", "phase7@example.invalid"], cwd=source)
                    run(["git", "config", "user.name", "CodePro Phase 7"], cwd=source)
                    (source / "value.py").write_text('def current_value():\n    return "before"\n', encoding="utf-8", newline="\n")
                    run(["git", "add", "."], cwd=source)
                    run(["git", "commit", "-m", "phase7-s3-base"], cwd=source)
                    revision = run(["git", "rev-parse", "HEAD"], cwd=source).stdout.strip()
                    isolated = IsolatedGitWorkspace.create(source_repository=source, revision=revision, workspace_root=workspaces, workspace_id="s3-task")

                    adapter_output = evidence / "autocoderover-result.json"
                    acr_output = evidence / "acr-native-output"
                    issue = 'In value.py, change current_value() so it returns the string "after" instead of "before". The change is limited to that function.'
                    executor_argv = (
                        str(acr_python),
                        str(ROOT / "tools" / "phase7_autocoderover_native.py"),
                        "--workspace", str(isolated.workspace),
                        "--revision", revision,
                        "--issue", issue,
                        "--model", MODEL_ALIAS,
                        "--base-url", BASE_URL,
                        "--output-dir", str(acr_output),
                        "--result", str(adapter_output),
                    )
                    env = os.environ.copy()
                    env["PYTHONPATH"] = str(UPSTREAM)
                    env["OPENAI_KEY"] = "local-llm"
                    env["OPENAI_API_KEY"] = "local-llm"
                    env["OPENAI_BASE_URL"] = BASE_URL
                    env["ACR_TOKEN_LIMIT"] = "768"

                    old_values = {key: os.environ.get(key) for key in ("PYTHONPATH", "OPENAI_KEY", "OPENAI_API_KEY", "OPENAI_BASE_URL", "ACR_TOKEN_LIMIT")}
                    try:
                        for key in old_values:
                            if key in env:
                                os.environ[key] = env[key]
                        result = run_vertical(
                            workspace=isolated.workspace, revision=revision, request_id="phase7-s3-autocoderover", task_id="phase7-trivial-edit",
                            requester_ref="user://phase7-compatibility", authority_ref="authority://phase7-compatibility", acceptance_authority_ref="acceptance://phase7-independent-verifier",
                            scope=("value.py",), candidate_files=("value.py",), affected_components=("fixture",), characterization_source_ref="evidence://phase7-s3-frozen-task",
                            executor_argv=executor_argv,
                            verifier_argv=(sys.executable, "-c", 'from pathlib import Path; ns={}; exec(Path("value.py").read_text(encoding="utf-8"), ns); ok=ns["current_value"]()=="after"; print("VERIFIER_OK" if ok else "VERIFIER_BAD"); raise SystemExit(0 if ok else 9)'),
                            evidence_dir=evidence / "vertical", max_wall_time_seconds=300,
                        )
                    finally:
                        for key, value in old_values.items():
                            if value is None:
                                os.environ.pop(key, None)
                            else:
                                os.environ[key] = value

                    vertical = result.to_dict()
                    summary["vertical"] = vertical
                    adapter = json.loads(adapter_output.read_text(encoding="utf-8")) if adapter_output.is_file() else {"error": {"type": "MissingAdapterEvidence", "message": "adapter output missing"}}
                    summary["adapter"] = adapter
                    run_root = Path(result.evidence_root)
                    patch_path = run_root / "workspace.patch"
                    patch_text = patch_path.read_text(encoding="utf-8", errors="replace") if patch_path.is_file() else ""
                    patch_ok = '-    return "before"' in patch_text and '+    return "after"' in patch_text
                    verifier_path = run_root / "verification-summary.json"
                    verifier = json.loads(verifier_path.read_text(encoding="utf-8")) if verifier_path.is_file() else {}
                    verifier_ok = verifier.get("status") == "PASSED"
                    stats = adapter.get("stats") if isinstance(adapter.get("stats"), dict) else {}
                    tool_calls = adapter.get("tool_calls") if isinstance(adapter.get("tool_calls"), list) else []
                    final_state = isolated.capture_state().to_dict()
                    source_state = capture_repository_state(source).to_dict()
                    cleanup = isolated.remove()
                    isolated = None

                    summary["telemetry"] = {
                        "model_calls_observed": stats.get("total_input_tokens", 0) > 0,
                        "prompt_tokens": stats.get("total_input_tokens"),
                        "completion_tokens": stats.get("total_output_tokens"),
                        "provider_api_cost_usd": stats.get("total_cost"),
                        "native_tool_call_count": len(tool_calls),
                    }
                    summary["gates"].update({
                        "explicit_local_binding": adapter.get("base_url", "").rstrip("/") == BASE_URL.rstrip("/"),
                        "model_calls_observed": stats.get("total_input_tokens", 0) > 0,
                        "native_tool_calls_observed": len(tool_calls) > 0,
                        "search_observed": any(item.get("func_name", "").startswith("search_") for item in tool_calls if isinstance(item, dict)),
                        "write_patch_observed": any(item.get("func_name") == "write_patch" for item in tool_calls if isinstance(item, dict)),
                        "edit_observed": adapter.get("patch_applied") is True,
                        "patch_captured": patch_ok,
                        "independent_verifier": verifier_ok,
                        "source_repository_unchanged": source_state.get("clean") is True,
                        "workspace_cleanup": cleanup.removed,
                    })
                    summary["repository_state"] = {"initial_revision": revision, "final": final_state, "source": source_state}
                    summary["classification"] = classify(vertical, adapter, verifier_ok, patch_ok)
                    write_json(evidence / "s3-summary.json", summary)
                    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
                    return 0
            finally:
                if isolated is not None:
                    try:
                        isolated.remove()
                    except Exception:
                        pass
                if process.poll() is None:
                    process.kill()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        pass
    except Exception as exc:
        if not (evidence / "s3-summary.json").exists():
            return block(evidence, summary, "BLOCKED_HARNESS_OR_ENVIRONMENT", "exception", {"type": type(exc).__name__, "message": str(exc)})
        raise


if __name__ == "__main__":
    raise SystemExit(main())
