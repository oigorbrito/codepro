#!/usr/bin/env python3
"""Run Phase 7 S2 Agentless compatibility against the frozen local runtime."""

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
from arkx.vertical import VerticalRunStatus, run_vertical  # noqa: E402

RUNTIME_ROOT = Path(r"D:\projetos\codepro-mini-runtime")
S2_ROOT = RUNTIME_ROOT / "phase7" / "S2-Agentless"
UPSTREAM = S2_ROOT / "upstream"
VENV = S2_ROOT / "venv"
INSTALL_MARKER = S2_ROOT / "installed.json"

UPSTREAM_URL = "https://github.com/OpenAutoCoder/Agentless.git"
VERSION = "v1.5.0"
COMMIT = "b150f28465a77a81a7f4776384957a4271f5bd69"

MODEL_SHA256 = "E0406663965846AE22A403456EB826CCCE5F450840491F71952F18A7CB78E7D5"
MODEL_BYTES = 2244011552
MODEL_ALIAS = "codepro-phase7-granite42-3b"
PORT = 18090
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


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def summary_base() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "phase": 7,
        "candidate": "S2",
        "scaffold": "Agentless",
        "version": VERSION,
        "commit": COMMIT,
        "classification": "BLOCKED_UNCLASSIFIED",
        "local_runtime": {"base_url": BASE_URL, "model_alias": MODEL_ALIAS, "fallback": "DISABLED"},
        "native_contract": "repair_prompt -> OpenAIChatDecoder -> Agentless edit parser -> repository patch",
        "native_command_loop": "NOT_APPLICABLE_AGENTLESS_PIPELINE",
        "gates": {},
        "telemetry": {},
        "vertical": None,
        "adapter": None,
        "selected_scaffold": False,
        "executor_promotion": "NOT_AUTHORIZED",
        "next_candidate": "S3",
    }


def block(evidence: Path, summary: dict[str, Any], classification: str, stage: str, detail: Any) -> int:
    summary["classification"] = classification
    summary["blocker"] = {"stage": stage, "detail": detail}
    write_json(evidence / "s2-summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def ensure_upstream(evidence: Path, summary: dict[str, Any]) -> bool:
    S2_ROOT.mkdir(parents=True, exist_ok=True)
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


def ensure_python311(summary: dict[str, Any]) -> Path | None:
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


def ensure_install(evidence: Path, base_python: Path, summary: dict[str, Any]) -> Path | None:
    python = venv_python()
    marker_ok = False
    if INSTALL_MARKER.is_file() and python.is_file():
        try:
            marker_ok = json.loads(INSTALL_MARKER.read_text(encoding="utf-8")).get("commit") == COMMIT
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
        installed = run([str(python), "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "-r", str(UPSTREAM / "requirements.txt")], timeout=3600, check=False)
        (evidence / "install-stdout.txt").write_text(installed.stdout, encoding="utf-8", newline="\n")
        (evidence / "install-stderr.txt").write_text(installed.stderr, encoding="utf-8", newline="\n")
        if installed.returncode != 0:
            summary["blocker"] = {"stage": "installation", "detail": installed.stderr[-4000:]}
            return None
        INSTALL_MARKER.write_text(json.dumps({"repository": UPSTREAM_URL, "version": VERSION, "commit": COMMIT, "python": str(python)}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    freeze = run([str(python), "-m", "pip", "freeze"], timeout=600, check=False)
    metadata = run([str(python), "-c", "from importlib.metadata import version; print(version('openai'))"], check=False)
    write_json(evidence / "installation.json", {"python": str(python.resolve()), "openai_version": metadata.stdout.strip() if metadata.returncode == 0 else None, "pip_freeze": freeze.stdout.splitlines()})
    summary["gates"]["installation"] = freeze.returncode == 0
    return python if summary["gates"]["installation"] else None


def verify_port() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", PORT))
    except OSError as exc:
        raise RuntimeError(f"explicit S2 port {PORT} unavailable") from exc
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
    if error and not adapter.get("model_call_observed"):
        return "BLOCKED_SCAFFOLD_OR_API_STARTUP"
    if adapter.get("model_call_observed") and not adapter.get("edit_applied"):
        return "BLOCKED_MODEL_EDIT_FORMAT"
    if vertical.get("status") == "VERIFIED" and adapter.get("edit_applied") and verifier_ok and patch_ok:
        return "COMPATIBLE"
    if vertical.get("status") == "TIMED_OUT":
        return "BLOCKED_TIMEOUT"
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
        py311 = ensure_python311(summary)
        if py311 is None:
            return block(evidence, summary, "BLOCKED_PYTHON_RUNTIME", "python_runtime", summary.get("blocker"))
        agentless_python = ensure_install(evidence, py311, summary)
        if agentless_python is None:
            return block(evidence, summary, "BLOCKED_INSTALLATION", "installation", summary.get("blocker"))

        model = find_model()
        server = find_server()
        verify_port()
        server_argv = [str(server), "-m", str(model), "--device", "CUDA0", "-ngl", "99", "-c", "4096", "--host", "127.0.0.1", "--port", str(PORT), "--alias", MODEL_ALIAS]
        write_json(evidence / "runtime-binding.json", {"llama_cpp_build": LLAMA_BUILD, "llama_cpp_commit": LLAMA_COMMIT, "server": str(server), "server_argv": server_argv, "base_url": BASE_URL, "model_alias": MODEL_ALIAS, "model_artifact": str(model), "model_bytes": model.stat().st_size, "model_sha256": sha256(model), "fallback": "DISABLED"})

        with (evidence / "llama-server-stdout.txt").open("w", encoding="utf-8", newline="\n") as out_handle, (evidence / "llama-server-stderr.txt").open("w", encoding="utf-8", newline="\n") as err_handle:
            process = subprocess.Popen(server_argv, cwd=server.parent, stdout=out_handle, stderr=err_handle, text=True, shell=False)
            isolated: IsolatedGitWorkspace | None = None
            old_env = {name: os.environ.get(name) for name in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "PYTHONPATH")}
            try:
                preflight = wait_server(process)
                summary["gates"]["local_runtime_ready"] = True
                write_json(evidence / "server-preflight.json", preflight)

                bind_env = os.environ.copy()
                bind_env["OPENAI_API_KEY"] = "local-llm"
                bind_env["OPENAI_BASE_URL"] = BASE_URL
                bind_probe = run([str(agentless_python), "-c", "from openai import OpenAI; c=OpenAI(); print(str(c.base_url))"], env=bind_env, check=False)
                observed_base = bind_probe.stdout.strip().rstrip("/")
                summary["gates"]["explicit_local_binding"] = bind_probe.returncode == 0 and observed_base == BASE_URL.rstrip("/")
                write_json(evidence / "openai-binding-preflight.json", {"returncode": bind_probe.returncode, "stdout": bind_probe.stdout, "stderr": bind_probe.stderr, "observed_base_url": observed_base, "expected_base_url": BASE_URL})
                if not summary["gates"]["explicit_local_binding"]:
                    return block(evidence, summary, "BLOCKED_LOCAL_ENDPOINT_BINDING", "openai_binding", {"stdout": bind_probe.stdout, "stderr": bind_probe.stderr})

                with tempfile.TemporaryDirectory(prefix="codepro-phase7-s2-", dir=S2_ROOT) as tmp:
                    base = Path(tmp)
                    source = base / "source"
                    workspaces = base / "workspaces"
                    source.mkdir()
                    run(["git", "init"], cwd=source)
                    run(["git", "config", "user.email", "phase7@example.invalid"], cwd=source)
                    run(["git", "config", "user.name", "CodePro Phase 7"], cwd=source)
                    (source / "value.py").write_text('VALUE = "before"\n', encoding="utf-8", newline="\n")
                    run(["git", "add", "."], cwd=source)
                    run(["git", "commit", "-m", "phase7-s2-base"], cwd=source)
                    revision = run(["git", "rev-parse", "HEAD"], cwd=source).stdout.strip()
                    isolated = IsolatedGitWorkspace.create(source_repository=source, revision=revision, workspace_root=workspaces, workspace_id="s2-task")

                    os.environ["OPENAI_API_KEY"] = "local-llm"
                    os.environ["OPENAI_BASE_URL"] = BASE_URL
                    os.environ["PYTHONPATH"] = str(UPSTREAM)
                    adapter_output = evidence / "agentless-result.json"
                    issue = 'Change the single assignment VALUE = "before" in value.py to VALUE = "after". Return an Agentless edit_file command for that one-line change.'
                    executor_argv = (str(agentless_python), str(ROOT / "tools" / "phase7_agentless_native.py"), "--target", "value.py", "--issue", issue, "--model", MODEL_ALIAS, "--output", str(adapter_output))
                    result = run_vertical(
                        workspace=isolated.workspace, revision=revision, request_id="phase7-s2-agentless", task_id="phase7-trivial-edit",
                        requester_ref="user://phase7-compatibility", authority_ref="authority://phase7-compatibility", acceptance_authority_ref="acceptance://phase7-independent-verifier",
                        scope=("value.py",), candidate_files=("value.py",), affected_components=("fixture",), characterization_source_ref="evidence://phase7-s2-frozen-task",
                        executor_argv=executor_argv,
                        verifier_argv=(sys.executable, "-c", 'from pathlib import Path; value=Path("value.py").read_text(encoding="utf-8").strip(); print("VERIFIER_OK" if value == \'VALUE = "after"\' else "VERIFIER_BAD"); raise SystemExit(0 if value == \'VALUE = "after"\' else 9)'),
                        evidence_dir=evidence / "vertical", max_wall_time_seconds=180,
                    )
                    vertical = result.to_dict()
                    summary["vertical"] = vertical
                    adapter = json.loads(adapter_output.read_text(encoding="utf-8")) if adapter_output.is_file() else {"error": {"type": "MissingAdapterEvidence", "message": "adapter output missing"}}
                    summary["adapter"] = adapter
                    run_root = Path(result.evidence_root)
                    patch_path = run_root / "workspace.patch"
                    patch_text = patch_path.read_text(encoding="utf-8", errors="replace") if patch_path.is_file() else ""
                    patch_ok = 'VALUE = "before"' in patch_text and 'VALUE = "after"' in patch_text
                    verifier_path = run_root / "verification-summary.json"
                    verifier = json.loads(verifier_path.read_text(encoding="utf-8")) if verifier_path.is_file() else {}
                    verifier_ok = verifier.get("status") == "PASSED"
                    final_state = isolated.capture_state().to_dict()
                    source_state = capture_repository_state(source).to_dict()
                    cleanup = isolated.remove()
                    isolated = None

                    usage = adapter.get("usage") if isinstance(adapter.get("usage"), dict) else {}
                    summary["telemetry"] = {"prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"), "model_calls": 1 if adapter.get("model_call_observed") else 0}
                    summary["gates"].update({
                        "inspect_observed": adapter.get("inspect_observed") is True,
                        "model_calls_observed": adapter.get("model_call_observed") is True,
                        "termination_observed": adapter.get("termination_observed") is True,
                        "native_edit_parser_observed": adapter.get("edit_parser_observed") is True,
                        "edit_observed": adapter.get("edit_applied") is True,
                        "patch_captured": patch_ok,
                        "verification_command_observed": verifier_path.is_file(),
                        "independent_verifier": verifier_ok,
                        "source_repository_unchanged": source_state.get("clean") is True,
                        "workspace_cleanup": cleanup.removed,
                    })
                    summary["repository_state"] = {"initial_revision": revision, "final": final_state, "source": source_state}
                    summary["classification"] = classify(vertical, adapter, verifier_ok, patch_ok)
                    write_json(evidence / "s2-summary.json", summary)
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
    except Exception as exc:
        if not (evidence / "s2-summary.json").exists():
            return block(evidence, summary, "BLOCKED_HARNESS_OR_ENVIRONMENT", "exception", {"type": type(exc).__name__, "message": str(exc)})
        raise


if __name__ == "__main__":
    raise SystemExit(main())
