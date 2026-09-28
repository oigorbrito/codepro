#!/usr/bin/env python3
"""Run Phase 7 S4 OpenHands Agent Canvas compatibility on Windows-native."""

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
from urllib.request import Request, urlopen

ROOT = Path(__file__).parents[1].resolve()
SRC = ROOT / "src"
if str(SRC) not in sys.path: sys.path.insert(0, str(SRC))
from arkx.isolated_workspace import IsolatedGitWorkspace, capture_repository_state  # noqa: E402
from arkx.vertical import run_vertical  # noqa: E402

RUNTIME_ROOT = Path(r"D:\projetos\codepro-mini-runtime")
S4_ROOT = RUNTIME_ROOT / "phase7" / "S4-OpenHands"
UPSTREAM = S4_ROOT / "upstream"
UPSTREAM_URL = "https://github.com/OpenHands/OpenHands.git"
VERSION = "v1.21.0"
COMMIT = "fc6d890f7b21c71a17de60d50597c00355e235ea"
AGENT_SERVER_VERSION = "1.49.3"
AUTOMATION_VERSION = "1.13.3"
MODEL_SHA256 = "E0406663965846AE22A403456EB826CCCE5F450840491F71952F18A7CB78E7D5"
MODEL_BYTES = 2244011552
MODEL_ALIAS = "codepro-phase7-granite42-3b"
LLAMA_PORT = 18092
LLAMA_BASE = f"http://127.0.0.1:{LLAMA_PORT}/v1"
CANVAS_PORT = 18400
AGENT_PORT = 18401
AUTOMATION_PORT = 18402
VSCODE_PORT = 19401
CANVAS_BASE = f"http://127.0.0.1:{CANVAS_PORT}"
SESSION_KEY = "codepro-phase7-s4-local-key"
LLAMA_BUILD = 11205
LLAMA_COMMIT = "95887577ab5fead779581a7030a83c7752ff3234"

def run(argv:list[str], *, cwd:Path|None=None, env:dict[str,str]|None=None, timeout:int=900, check:bool=True)->subprocess.CompletedProcess[str]:
    p=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,text=True,encoding="utf-8",errors="replace",shell=False,check=False,timeout=timeout)
    if check and p.returncode!=0: raise RuntimeError(f"command failed ({p.returncode}): {argv!r}\nstdout={p.stdout[-4000:]}\nstderr={p.stderr[-4000:]}")
    return p

def write_json(path:Path,value:Any)->None:
    if path.exists(): raise FileExistsError(f"refusing to overwrite evidence: {path}")
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")

def sha256(path:Path)->str:
    d=hashlib.sha256()
    with path.open("rb") as h:
        for chunk in iter(lambda:h.read(1024*1024),b""): d.update(chunk)
    return d.hexdigest().upper()

def summary_base()->dict[str,Any]:
    return {"schema_version":1,"phase":7,"candidate":"S4","scaffold":"OpenHands Agent Canvas","version":VERSION,"commit":COMMIT,
            "agent_server_version":AGENT_SERVER_VERSION,"automation_version":AUTOMATION_VERSION,"classification":"BLOCKED_UNCLASSIFIED",
            "local_runtime":{"base_url":LLAMA_BASE,"model_alias":MODEL_ALIAS,"fallback":"DISABLED"},
            "native_contract":"Agent Canvas request builder -> Agent Server 1.49.3 -> OpenHands agent tools -> isolated repository -> CodePro verifier",
            "gates":{},"telemetry":{},"vertical":None,"adapter":None,"selected_scaffold":False,"executor_promotion":"NOT_AUTHORIZED"}

def block(evidence:Path,summary:dict[str,Any],classification:str,stage:str,detail:Any)->int:
    summary["classification"]=classification; summary["blocker"]={"stage":stage,"detail":detail}
    write_json(evidence/"s4-summary.json",summary); print(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)); return 0

def ensure_upstream(evidence:Path,summary:dict[str,Any])->bool:
    S4_ROOT.mkdir(parents=True,exist_ok=True)
    if not UPSTREAM.exists():
        p=run(["git","clone",UPSTREAM_URL,str(UPSTREAM)],timeout=1200,check=False)
        write_json(evidence/"clone.json",{"returncode":p.returncode,"stdout":p.stdout,"stderr":p.stderr})
        if p.returncode!=0: summary["blocker"]={"stage":"clone","detail":p.stderr[-4000:]}; return False
    status=run(["git","-C",str(UPSTREAM),"status","--porcelain=v1"],check=False)
    if status.returncode!=0 or status.stdout.strip(): summary["blocker"]={"stage":"upstream_cleanliness","detail":status.stdout+status.stderr}; return False
    fetch=run(["git","-C",str(UPSTREAM),"fetch","--tags","--prune","origin"],timeout=1200,check=False)
    if fetch.returncode!=0: summary["blocker"]={"stage":"fetch","detail":fetch.stderr[-4000:]}; return False
    checkout=run(["git","-C",str(UPSTREAM),"checkout","--detach",COMMIT],check=False)
    if checkout.returncode!=0: summary["blocker"]={"stage":"checkout","detail":checkout.stderr[-4000:]}; return False
    head=run(["git","-C",str(UPSTREAM),"rev-parse","HEAD"]).stdout.strip()
    package=json.loads((UPSTREAM/"package.json").read_text(encoding="utf-8"))
    defaults=json.loads((UPSTREAM/"config"/"defaults.json").read_text(encoding="utf-8"))
    identity={"repository":UPSTREAM_URL,"commit":head,"package_version":package.get("version"),"agent_server_version":defaults.get("versions",{}).get("agentServer"),"automation_version":defaults.get("versions",{}).get("automation")}
    write_json(evidence/"upstream-identity.json",identity)
    ok=head==COMMIT and package.get("version")=="1.21.0" and identity["agent_server_version"]==AGENT_SERVER_VERSION and identity["automation_version"]==AUTOMATION_VERSION
    summary["gates"]["exact_upstream_identity"]=ok; return ok

def ensure_install(evidence:Path,summary:dict[str,Any])->bool:
    node=shutil.which("node.exe") or shutil.which("node"); npm=shutil.which("npm.cmd") or shutil.which("npm"); uvx=shutil.which("uvx.exe") or shutil.which("uvx")
    probes={}
    for name,exe in (("node",node),("npm",npm),("uvx",uvx)):
        if exe:
            p=run([exe,"--version"],check=False); probes[name]={"path":exe,"returncode":p.returncode,"stdout":p.stdout.strip(),"stderr":p.stderr.strip()}
        else: probes[name]={"path":None}
    write_json(evidence/"prerequisites.json",probes)
    if not node or not npm: summary["blocker"]={"stage":"node_npm","detail":probes}; return False
    if not uvx: summary["classification_hint"]="BLOCKED_PREREQUISITE_UVX"; summary["blocker"]={"stage":"uvx","detail":"uvx not found on PATH"}; return False
    install=run([npm,"ci","--no-audit","--no-fund"],cwd=UPSTREAM,timeout=5400,check=False)
    (evidence/"install-stdout.txt").write_text(install.stdout,encoding="utf-8",newline="\n")
    (evidence/"install-stderr.txt").write_text(install.stderr,encoding="utf-8",newline="\n")
    summary["gates"]["exact_npm_ci"]=install.returncode==0
    if install.returncode!=0: summary["blocker"]={"stage":"npm_ci","returncode":install.returncode,"stdout_tail":install.stdout[-4000:],"stderr_tail":install.stderr[-6000:]}; return False
    vite=UPSTREAM/"node_modules"/".bin"/("vite-node.cmd" if os.name=="nt" else "vite-node")
    summary["gates"]["vite_node_available"]=vite.is_file()
    if not vite.is_file(): summary["blocker"]={"stage":"vite_node","detail":str(vite)}; return False
    return True

def find_model()->Path:
    for p in (RUNTIME_ROOT/"models"/"phase4").rglob("*.gguf"):
        if p.stat().st_size==MODEL_BYTES and sha256(p)==MODEL_SHA256: return p.resolve()
    raise RuntimeError("frozen L3 artifact not found by SHA256")

def find_server()->Path:
    matches=list((RUNTIME_ROOT/"downloads"/"llama-b11205-bin-win-cuda-13.4-x64").rglob("llama-server.exe"))
    if not matches: raise RuntimeError("frozen llama-server.exe not found")
    return matches[0].resolve()

def assert_ports()->None:
    for port in (LLAMA_PORT,CANVAS_PORT,AGENT_PORT,AUTOMATION_PORT,VSCODE_PORT):
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try: s.bind(("127.0.0.1",port))
        except OSError as exc: raise RuntimeError(f"explicit Phase 7 S4 port {port} unavailable") from exc
        finally: s.close()

def get_json(url:str,headers:dict[str,str]|None=None,timeout:float=3)->Any:
    req=Request(url,headers=headers or {})
    with urlopen(req,timeout=timeout) as r: return json.loads(r.read().decode("utf-8"))

def wait_llama(process:subprocess.Popen[Any],timeout_seconds:int=120)->dict[str,Any]:
    deadline=time.monotonic()+timeout_seconds; last=""
    while time.monotonic()<deadline:
        if process.poll() is not None: raise RuntimeError(f"llama-server exited early: {process.returncode}")
        try:
            health=get_json(f"{LLAMA_BASE}/health"); models=get_json(f"{LLAMA_BASE}/models"); ids=[x.get("id") for x in models.get("data",[]) if isinstance(x,dict)]
            if health.get("status")=="ok" and MODEL_ALIAS in ids: return {"health":health,"models":models}
        except Exception as exc: last=f"{type(exc).__name__}: {exc}"
        time.sleep(.5)
    raise RuntimeError(f"llama readiness timeout: {last}")

def wait_canvas(process:subprocess.Popen[Any],timeout_seconds:int=180)->dict[str,Any]:
    deadline=time.monotonic()+timeout_seconds; last=""
    headers={"X-Session-API-Key":SESSION_KEY}
    while time.monotonic()<deadline:
        if process.poll() is not None: raise RuntimeError(f"agent-canvas exited early: {process.returncode}")
        for path in ("/ready","/health","/server_info"):
            try:
                value=get_json(CANVAS_BASE+path,headers=headers,timeout=3)
                return {"path":path,"response":value}
            except Exception as exc: last=f"{path}: {type(exc).__name__}: {exc}"
        time.sleep(1)
    raise RuntimeError(f"agent-canvas readiness timeout: {last}")

def terminate_tree(process:subprocess.Popen[Any]|None)->None:
    if process is None or process.poll() is not None: return
    if os.name=="nt":
        subprocess.run(["taskkill","/PID",str(process.pid),"/T","/F"],capture_output=True,text=True,check=False)
    else:
        process.kill()
    try: process.wait(timeout=15)
    except subprocess.TimeoutExpired: pass

def token_usage(adapter:dict[str,Any])->dict[str,Any]:
    info=adapter.get("conversation_info") if isinstance(adapter.get("conversation_info"),dict) else {}
    metrics=info.get("metrics") if isinstance(info.get("metrics"),dict) else {}
    usage=metrics.get("accumulated_token_usage") if isinstance(metrics.get("accumulated_token_usage"),dict) else {}
    return {"prompt_tokens":usage.get("prompt_tokens"),"completion_tokens":usage.get("completion_tokens"),"context_window":usage.get("context_window")}

def classify(vertical:dict[str,Any],adapter:dict[str,Any],gates:dict[str,Any])->str:
    usage=token_usage(adapter); model_calls=isinstance(usage.get("prompt_tokens"),int) and usage.get("prompt_tokens",0)>0
    if adapter.get("error") and not adapter.get("conversation_id"): return "BLOCKED_OPENHANDS_REQUEST_OR_STARTUP"
    if model_calls and not gates.get("edit_observed"): return "BLOCKED_MODEL_TOOL_PROTOCOL"
    if vertical.get("status")=="VERIFIED" and all(gates.get(k) is True for k in ("edit_observed","patch_captured","independent_verifier")): return "COMPATIBLE"
    if vertical.get("status")=="TIMED_OUT": return "BLOCKED_TIMEOUT"
    if vertical.get("status")=="ENVIRONMENT_UNAVAILABLE": return "BLOCKED_ENVIRONMENT"
    return "INCOMPATIBLE"

def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--evidence-dir",required=True); args=parser.parse_args(argv)
    evidence=Path(args.evidence_dir).expanduser().resolve()
    if evidence.exists() and any(evidence.iterdir()): raise SystemExit(f"refusing to overwrite non-empty evidence directory: {evidence}")
    evidence.mkdir(parents=True,exist_ok=True); summary=summary_base()
    llama_proc=None; canvas_proc=None; isolated=None
    try:
        if not ensure_upstream(evidence,summary): return block(evidence,summary,"BLOCKED_UPSTREAM_IDENTITY","upstream",summary.get("blocker"))
        if not ensure_install(evidence,summary):
            hint=summary.pop("classification_hint",None)
            return block(evidence,summary,hint or "BLOCKED_INSTALLATION_WINDOWS_NATIVE","installation",summary.get("blocker"))
        assert_ports(); model=find_model(); server=find_server()
        llama_argv=[str(server),"-m",str(model),"--device","CUDA0","-ngl","99","-c","4096","--host","127.0.0.1","--port",str(LLAMA_PORT),"--alias",MODEL_ALIAS]
        write_json(evidence/"runtime-binding.json",{"llama_cpp_build":LLAMA_BUILD,"llama_cpp_commit":LLAMA_COMMIT,"server_argv":llama_argv,"base_url":LLAMA_BASE,"model_alias":MODEL_ALIAS,"model_artifact":str(model),"model_bytes":model.stat().st_size,"model_sha256":sha256(model),"fallback":"DISABLED"})
        llama_out=(evidence/"llama-server-stdout.txt").open("w",encoding="utf-8",newline="\n"); llama_err=(evidence/"llama-server-stderr.txt").open("w",encoding="utf-8",newline="\n")
        llama_proc=subprocess.Popen(llama_argv,cwd=server.parent,stdout=llama_out,stderr=llama_err,text=True,shell=False)
        write_json(evidence/"llama-preflight.json",wait_llama(llama_proc)); summary["gates"]["local_runtime_ready"]=True
        with tempfile.TemporaryDirectory(prefix="codepro-phase7-s4-",dir=S4_ROOT) as tmp:
            base=Path(tmp); source=base/"source"; workspaces=base/"workspaces"; state=base/"canvas-state"; profile=base/"profile"; source.mkdir(); state.mkdir(); profile.mkdir()
            (profile/"AppData"/"Local").mkdir(parents=True); (profile/"AppData"/"Roaming").mkdir(parents=True); (profile/".cache").mkdir(parents=True)
            run(["git","init"],cwd=source); run(["git","config","user.email","phase7@example.invalid"],cwd=source); run(["git","config","user.name","CodePro Phase 7"],cwd=source)
            (source/"value.py").write_text('VALUE = "before"\n',encoding="utf-8",newline="\n"); run(["git","add","."],cwd=source); run(["git","commit","-m","phase7-s4-base"],cwd=source)
            revision=run(["git","rev-parse","HEAD"],cwd=source).stdout.strip(); isolated=IsolatedGitWorkspace.create(source_repository=source,revision=revision,workspace_root=workspaces,workspace_id="s4-task")
            node=shutil.which("node.exe") or shutil.which("node"); assert node
            canvas_env=os.environ.copy(); canvas_env.update({
                "LOCAL_BACKEND_API_KEY":SESSION_KEY,
                "OH_AGENT_SERVER_VERSION":AGENT_SERVER_VERSION,
                "OH_AUTOMATION_VERSION":AUTOMATION_VERSION,
                "OH_CANVAS_SAFE_BACKEND_PORT":str(AGENT_PORT),
                "OH_CANVAS_SAFE_AUTOMATION_PORT":str(AUTOMATION_PORT),
                "OH_CANVAS_SAFE_VSCODE_PORT":str(VSCODE_PORT),
                "OH_CANVAS_SAFE_STATE_DIR":str(state),
                "OH_SESSION_API_KEY_PATH":str(state/"session-api-key.txt"),
                "HOME":str(profile),
                "USERPROFILE":str(profile),
                "LOCALAPPDATA":str(profile/"AppData"/"Local"),
                "APPDATA":str(profile/"AppData"/"Roaming"),
                "XDG_CACHE_HOME":str(profile/".cache"),
                "VITE_DO_NOT_TRACK":"1",
                "NO_COLOR":"1",
            })
            canvas_argv=[node,str(UPSTREAM/"bin"/"agent-canvas.mjs"),"--backend-only","--port",str(CANVAS_PORT)]
            write_json(evidence/"canvas-binding.json",{"argv":canvas_argv,"canvas_version":"1.21.0","agent_server_version":AGENT_SERVER_VERSION,"automation_version":AUTOMATION_VERSION,"ingress":CANVAS_BASE,"agent_port":AGENT_PORT,"automation_port":AUTOMATION_PORT,"vscode_port":VSCODE_PORT,"state_dir":str(state),"profile_dir":str(profile),"profile_isolation":"PROCESS_ENVIRONMENT_ONLY","session_key":"REDACTED"})
            canvas_out=(evidence/"agent-canvas-stdout.txt").open("w",encoding="utf-8",newline="\n"); canvas_err=(evidence/"agent-canvas-stderr.txt").open("w",encoding="utf-8",newline="\n")
            canvas_proc=subprocess.Popen(canvas_argv,cwd=UPSTREAM,env=canvas_env,stdout=canvas_out,stderr=canvas_err,text=True,shell=False)
            write_json(evidence/"canvas-preflight.json",wait_canvas(canvas_proc)); summary["gates"]["agent_canvas_ready"]=True
            result_path=evidence/"openhands-result.json"
            issue="Work only in the current repository. Inspect value.py and confirm it contains VALUE = \"before\". Change it to VALUE = \"after\". Then run a Python command that imports value and asserts value.VALUE == \"after\". Finish after the check succeeds."
            executor=(sys.executable,str(ROOT/"tools"/"phase7_openhands_executor.py"),"--upstream",str(UPSTREAM),"--backend-url",CANVAS_BASE,"--api-key",SESSION_KEY,"--working-dir",str(isolated.workspace),"--llm-base-url",LLAMA_BASE,"--model-alias",MODEL_ALIAS,"--result",str(result_path),"--issue",issue)
            vr=run_vertical(workspace=isolated.workspace,revision=revision,request_id="phase7-s4-openhands",task_id="phase7-trivial-edit",requester_ref="user://phase7-compatibility",authority_ref="authority://phase7-compatibility",acceptance_authority_ref="acceptance://phase7-independent-verifier",scope=("value.py",),candidate_files=("value.py",),affected_components=("fixture",),characterization_source_ref="evidence://phase7-s4-frozen-task",executor_argv=executor,verifier_argv=(sys.executable,"-c",'from pathlib import Path; ns={}; exec(Path("value.py").read_text(encoding="utf-8"),ns); ok=ns.get("VALUE")=="after"; print("VERIFIER_OK" if ok else "VERIFIER_BAD"); raise SystemExit(0 if ok else 9)'),evidence_dir=evidence/"vertical",max_wall_time_seconds=320)
            vertical=vr.to_dict(); summary["vertical"]=vertical
            adapter=json.loads(result_path.read_text(encoding="utf-8")) if result_path.is_file() else {"error":{"type":"MissingAdapterEvidence","message":"OpenHands harness result missing"}}; summary["adapter"]=adapter
            obs=adapter.get("observations") if isinstance(adapter.get("observations"),dict) else {}
            run_root=Path(vr.evidence_root); patch_path=run_root/"workspace.patch"; patch_text=patch_path.read_text(encoding="utf-8",errors="replace") if patch_path.is_file() else ""
            patch_ok='-VALUE = "before"' in patch_text and '+VALUE = "after"' in patch_text
            verifier_path=run_root/"verification-summary.json"; verifier=json.loads(verifier_path.read_text(encoding="utf-8")) if verifier_path.is_file() else {}; verifier_ok=verifier.get("status")=="PASSED"
            usage=token_usage(adapter); summary["telemetry"]={**usage,"provider_api_cost_usd":0}
            final_state=isolated.capture_state().to_dict(); source_state=capture_repository_state(source).to_dict(); cleanup=isolated.remove(); isolated=None
            summary["gates"].update({"explicit_local_binding":(adapter.get("llm_binding") or {}).get("base_url")==LLAMA_BASE and (adapter.get("llm_binding") or {}).get("model")==f"openai/{MODEL_ALIAS}","model_calls_observed":isinstance(usage.get("prompt_tokens"),int) and usage.get("prompt_tokens",0)>0,"inspect_observed":obs.get("inspectObserved") is True,"command_observed":obs.get("commandObserved") is True,"event_edit_signal":obs.get("editObserved") is True,"edit_observed":len(vertical.get("changed_files") or [])>0,"termination_observed":str(adapter.get("execution_status") or "").lower() in {"finished","error","stuck","stopped"},"patch_captured":patch_ok,"independent_verifier":verifier_ok,"source_repository_unchanged":source_state.get("clean") is True,"workspace_cleanup":cleanup.removed})
            summary["repository_state"]={"initial_revision":revision,"final":final_state,"source":source_state}; summary["classification"]=classify(vertical,adapter,summary["gates"])
            write_json(evidence/"s4-summary.json",summary); print(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)); return 0
    except Exception as exc:
        if not (evidence/"s4-summary.json").exists(): return block(evidence,summary,"BLOCKED_HARNESS_OR_ENVIRONMENT","exception",{"type":type(exc).__name__,"message":str(exc)})
        raise
    finally:
        if isolated is not None:
            try: isolated.remove()
            except Exception: pass
        terminate_tree(canvas_proc); terminate_tree(llama_proc)
        for handle_name in ("canvas_out","canvas_err","llama_out","llama_err"):
            handle=locals().get(handle_name)
            if handle:
                try: handle.close()
                except Exception: pass

if __name__=="__main__": raise SystemExit(main())
