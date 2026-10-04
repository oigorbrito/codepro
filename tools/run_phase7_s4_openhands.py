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

def summary_base(*, model_alias:str=MODEL_ALIAS)->dict[str,Any]:
    return {"schema_version":1,"phase":7,"candidate":"S4","scaffold":"OpenHands Agent Canvas","version":VERSION,"commit":COMMIT,
            "agent_server_version":AGENT_SERVER_VERSION,"automation_version":AUTOMATION_VERSION,"classification":"BLOCKED_UNCLASSIFIED",
            "local_runtime":{"base_url":LLAMA_BASE,"model_alias":model_alias,"fallback":"DISABLED"},
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
    generate=run([npm,"run","make-i18n"],cwd=UPSTREAM,timeout=900,check=False)
    (evidence/"make-i18n-stdout.txt").write_text(generate.stdout,encoding="utf-8",newline="\n")
    (evidence/"make-i18n-stderr.txt").write_text(generate.stderr,encoding="utf-8",newline="\n")
    declaration=UPSTREAM/"src"/"i18n"/"declaration.ts"
    summary["gates"]["generated_i18n"]=generate.returncode==0 and declaration.is_file()
    if not summary["gates"]["generated_i18n"]:
        summary["blocker"]={"stage":"make_i18n","returncode":generate.returncode,"declaration_exists":declaration.is_file(),"stdout_tail":generate.stdout[-4000:],"stderr_tail":generate.stderr[-6000:]}; return False
    vite=UPSTREAM/"node_modules"/".bin"/("vite-node.cmd" if os.name=="nt" else "vite-node")
    summary["gates"]["vite_node_available"]=vite.is_file()
    if not vite.is_file(): summary["blocker"]={"stage":"vite_node","detail":str(vite)}; return False
    return True

def find_model(*, model_path:str|None=None, model_bytes:int=MODEL_BYTES, model_sha256:str=MODEL_SHA256)->Path:
    expected_sha=model_sha256.upper()
    if model_path is not None:
        p=Path(model_path).expanduser().resolve()
        if not p.is_file(): raise RuntimeError(f"frozen model artifact not found: {p}")
        if p.stat().st_size!=model_bytes: raise RuntimeError(f"frozen model byte-size mismatch: {p}")
        if sha256(p)!=expected_sha: raise RuntimeError(f"frozen model SHA256 mismatch: {p}")
        return p
    for p in (RUNTIME_ROOT/"models"/"phase4").rglob("*.gguf"):
        if p.stat().st_size==model_bytes and sha256(p)==expected_sha: return p.resolve()
    raise RuntimeError("frozen model artifact not found by SHA256")

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

def wait_llama(process:subprocess.Popen[Any],model_alias:str=MODEL_ALIAS,timeout_seconds:int=120)->dict[str,Any]:
    deadline=time.monotonic()+timeout_seconds; last=""
    while time.monotonic()<deadline:
        if process.poll() is not None: raise RuntimeError(f"llama-server exited early: {process.returncode}")
        try:
            health=get_json(f"{LLAMA_BASE}/health"); models=get_json(f"{LLAMA_BASE}/models"); ids=[x.get("id") for x in models.get("data",[]) if isinstance(x,dict)]
            if health.get("status")=="ok" and model_alias in ids: return {"health":health,"models":models}
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
    stats=info.get("stats") if isinstance(info.get("stats"),dict) else {}
    per_usage=stats.get("usage_to_metrics") if isinstance(stats.get("usage_to_metrics"),dict) else {}
    prompt=0; completion=0; context_windows=[]
    observed=False
    for metrics in per_usage.values():
        if not isinstance(metrics,dict): continue
        usage=metrics.get("accumulated_token_usage")
        if not isinstance(usage,dict): continue
        observed=True
        prompt += int(usage.get("prompt_tokens") or 0)
        completion += int(usage.get("completion_tokens") or 0)
        if isinstance(usage.get("context_window"),int): context_windows.append(usage["context_window"])
    return {"prompt_tokens":prompt if observed else None,"completion_tokens":completion if observed else None,"context_window":max(context_windows) if context_windows else None}

def model_call_observed(adapter:dict[str,Any])->bool|None:
    info=adapter.get("conversation_info") if isinstance(adapter.get("conversation_info"),dict) else {}
    stats=info.get("stats") if isinstance(info.get("stats"),dict) else {}
    per_usage=stats.get("usage_to_metrics") if isinstance(stats.get("usage_to_metrics"),dict) else {}
    saw_metrics=False
    for metrics in per_usage.values():
        if not isinstance(metrics,dict): continue
        saw_metrics=True
        latencies=metrics.get("response_latencies")
        if isinstance(latencies,list) and any(isinstance(x,dict) and str(x.get("response_id") or "").strip() for x in latencies):
            return True
        token_usages=metrics.get("token_usages")
        if isinstance(token_usages,list) and token_usages:
            return True
        usage=metrics.get("accumulated_token_usage")
        if isinstance(usage,dict) and (int(usage.get("prompt_tokens") or 0)>0 or int(usage.get("completion_tokens") or 0)>0):
            return True
    return False if saw_metrics else None

def classify(vertical:dict[str,Any],adapter:dict[str,Any],gates:dict[str,Any])->str:
    usage=token_usage(adapter); model_calls=model_call_observed(adapter)
    error=adapter.get("error") if isinstance(adapter.get("error"),dict) else {}
    error_message=str(error.get("message") or "").lower()
    if vertical.get("status")=="TIMED_OUT" or (adapter.get("conversation_id") and "timed out" in error_message): return "BLOCKED_TIMEOUT"
    if adapter.get("error") and not adapter.get("conversation_id"): return "BLOCKED_BEFORE_MODEL_CALL"
    if model_calls is None: return "BLOCKED_BEFORE_MODEL_CALL"
    if model_calls is False: return "BLOCKED_BEFORE_MODEL_CALL"
    if gates.get("system_prompt_profile_observed") is False: return "BLOCKED_TREATMENT_NOT_OBSERVED"
    if gates.get("max_iterations_observed") is False: return "BLOCKED_TREATMENT_NOT_OBSERVED"
    if model_calls and not gates.get("edit_observed"): return "BLOCKED_MODEL_TOOL_PROTOCOL"
    if vertical.get("status")=="VERIFIED" and all(gates.get(k) is True for k in ("platform_contract_observed","system_prompt_profile_observed","max_iterations_observed","model_calls_observed","inspect_observed","edit_observed","patch_captured","independent_verifier","termination_observed","source_repository_unchanged","workspace_cleanup")): return "COMPATIBLE"
    if vertical.get("status")=="ENVIRONMENT_UNAVAILABLE": return "BLOCKED_RUNTIME"
    if vertical.get("reason")=="CHANGED_FILES_OUTSIDE_AUTHORIZED_SCOPE": return "BLOCKED_SCOPE_VIOLATION"
    if not gates.get("patch_captured"): return "BLOCKED_NO_OBSERVABLE_CHANGE"
    return "INCOMPATIBLE"

def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--evidence-dir",required=True); parser.add_argument("--llama-parallel",type=int,default=None); parser.add_argument("--llama-context",type=int,default=4096); parser.add_argument("--litellm-version",default=None); parser.add_argument("--completion-log-dir",default=None); parser.add_argument("--study-id",default="phase7"); parser.add_argument("--conversation-timeout-seconds",type=int,default=240); parser.add_argument("--executor-timeout-seconds",type=int,default=280); parser.add_argument("--vertical-wall-time-seconds",type=int,default=320); parser.add_argument("--platform-contract",choices=("windows-powershell-v1","windows-powershell-v2"),default=None); parser.add_argument("--system-prompt-profile",choices=("windows-minimal-v1","windows-embedded-v1"),default=None); parser.add_argument("--conversation-worktree",choices=("true","false"),default="true"); parser.add_argument("--cleanup-untracked-python-bytecode",choices=("true","false"),default="false"); parser.add_argument("--max-iterations",type=int,default=8); parser.add_argument("--model-path",default=None); parser.add_argument("--model-bytes",type=int,default=MODEL_BYTES); parser.add_argument("--model-sha256",default=MODEL_SHA256); parser.add_argument("--model-alias",default=MODEL_ALIAS); args=parser.parse_args(argv)
    evidence=Path(args.evidence_dir).expanduser().resolve()
    if evidence.exists() and any(evidence.iterdir()): raise SystemExit(f"refusing to overwrite non-empty evidence directory: {evidence}")
    evidence.mkdir(parents=True,exist_ok=True); summary=summary_base(model_alias=args.model_alias); summary["study_id"]=args.study_id
    llama_proc=None; canvas_proc=None; isolated=None
    try:
        if not ensure_upstream(evidence,summary): return block(evidence,summary,"BLOCKED_UPSTREAM_IDENTITY","upstream",summary.get("blocker"))
        if not ensure_install(evidence,summary):
            summary.pop("classification_hint",None)
            return block(evidence,summary,"BLOCKED_INSTALLATION_WINDOWS_NATIVE","installation",summary.get("blocker"))
        if args.conversation_timeout_seconds < 1: raise ValueError("--conversation-timeout-seconds must be >= 1")
        if args.executor_timeout_seconds <= args.conversation_timeout_seconds: raise ValueError("--executor-timeout-seconds must be greater than --conversation-timeout-seconds")
        if args.vertical_wall_time_seconds <= args.executor_timeout_seconds: raise ValueError("--vertical-wall-time-seconds must be greater than --executor-timeout-seconds")
        if args.max_iterations < 1: raise ValueError("--max-iterations must be >= 1")
        summary["timeouts"]={"conversation_poll_seconds":args.conversation_timeout_seconds,"executor_process_seconds":args.executor_timeout_seconds,"vertical_wall_seconds":args.vertical_wall_time_seconds}
        summary["max_iterations_requested"]=args.max_iterations
        assert_ports(); model=find_model(model_path=args.model_path,model_bytes=args.model_bytes,model_sha256=args.model_sha256); server=find_server()
        if args.llama_context < 1: raise ValueError("--llama-context must be >= 1")
        llama_argv=[str(server),"-m",str(model),"--device","CUDA0","-ngl","99","-c",str(args.llama_context),"--host","127.0.0.1","--port",str(LLAMA_PORT),"--alias",args.model_alias]
        if args.llama_parallel is not None:
            if args.llama_parallel < 1: raise ValueError("--llama-parallel must be >= 1")
            llama_argv += ["--parallel",str(args.llama_parallel)]
            summary["local_runtime"]["parallel"]=args.llama_parallel
        try:
            context_index=llama_argv.index("-c")+1
            effective_context=int(llama_argv[context_index])
        except (ValueError, IndexError) as exc:
            raise RuntimeError("llama context binding is missing or invalid") from exc
        if effective_context != args.llama_context:
            raise RuntimeError(f"llama context binding mismatch: declared={args.llama_context} effective={effective_context}")
        summary["local_runtime"]["context_size"]=effective_context
        write_json(evidence/"runtime-binding.json",{"llama_cpp_build":LLAMA_BUILD,"llama_cpp_commit":LLAMA_COMMIT,"server_argv":llama_argv,"base_url":LLAMA_BASE,"model_alias":args.model_alias,"model_artifact":str(model),"model_bytes":model.stat().st_size,"model_sha256":sha256(model),"context_size":effective_context,"parallel":args.llama_parallel,"fallback":"DISABLED"})
        llama_out=(evidence/"llama-server-stdout.txt").open("w",encoding="utf-8",newline="\n"); llama_err=(evidence/"llama-server-stderr.txt").open("w",encoding="utf-8",newline="\n")
        llama_proc=subprocess.Popen(llama_argv,cwd=server.parent,stdout=llama_out,stderr=llama_err,text=True,shell=False)
        write_json(evidence/"llama-preflight.json",wait_llama(llama_proc,args.model_alias)); summary["gates"]["local_runtime_ready"]=True
        with tempfile.TemporaryDirectory(prefix="codepro-phase7-s4-",dir=S4_ROOT,ignore_cleanup_errors=True) as tmp:
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
            if args.litellm_version is not None:
                constraint_path=base/"uv-constraints.txt"
                constraint_path.write_text(f"litellm=={args.litellm_version}\n",encoding="utf-8",newline="\n")
                canvas_env["UV_CONSTRAINT"]=str(constraint_path)
                summary["local_runtime"]["litellm_constraint"]=args.litellm_version
            canvas_argv=[node,str(UPSTREAM/"bin"/"agent-canvas.mjs"),"--backend-only","--port",str(CANVAS_PORT)]
            write_json(evidence/"canvas-binding.json",{"argv":canvas_argv,"canvas_version":"1.21.0","agent_server_version":AGENT_SERVER_VERSION,"automation_version":AUTOMATION_VERSION,"ingress":CANVAS_BASE,"agent_port":AGENT_PORT,"automation_port":AUTOMATION_PORT,"vscode_port":VSCODE_PORT,"state_dir":str(state),"profile_dir":str(profile),"profile_isolation":"PROCESS_ENVIRONMENT_ONLY","uv_constraint":args.litellm_version,"session_key":"REDACTED"})
            canvas_out=(evidence/"agent-canvas-stdout.txt").open("w",encoding="utf-8",newline="\n"); canvas_err=(evidence/"agent-canvas-stderr.txt").open("w",encoding="utf-8",newline="\n")
            canvas_proc=subprocess.Popen(canvas_argv,cwd=UPSTREAM,env=canvas_env,stdout=canvas_out,stderr=canvas_err,text=True,shell=False)
            write_json(evidence/"canvas-preflight.json",wait_canvas(canvas_proc)); summary["gates"]["agent_canvas_ready"]=True
            result_path=evidence/"openhands-result.json"
            issue="Work only in the current repository. Inspect value.py and confirm it contains VALUE = \"before\". Change it to VALUE = \"after\". Then run a Python command that imports value and asserts value.VALUE == \"after\". Finish after the check succeeds."
            executor=[sys.executable,str(ROOT/"tools"/"phase7_openhands_executor.py"),"--upstream",str(UPSTREAM),"--backend-url",CANVAS_BASE,"--api-key",SESSION_KEY,"--working-dir",str(isolated.workspace),"--llm-base-url",LLAMA_BASE,"--model-alias",args.model_alias,"--result",str(result_path),"--issue",issue,"--poll-timeout-seconds",str(args.conversation_timeout_seconds),"--process-timeout-seconds",str(args.executor_timeout_seconds),"--conversation-worktree",args.conversation_worktree,"--cleanup-untracked-python-bytecode",args.cleanup_untracked_python_bytecode,"--max-iterations",str(args.max_iterations)]
            summary["conversation_worktree"]={"openhands_nested":args.conversation_worktree=="true","codepro_isolated_workspace":True}
            summary["workspace_ephemeral_cleanup_policy"]="untracked-python-bytecode-only-v1" if args.cleanup_untracked_python_bytecode=="true" else None
            if args.platform_contract is not None:
                executor += ["--platform-contract",args.platform_contract]
                summary["platform_contract"]={"id":args.platform_contract,"transport":"agent_context.system_message_suffix"}
            if args.system_prompt_profile is not None:
                executor += ["--system-prompt-profile",args.system_prompt_profile]
                summary["system_prompt_profile"]={"id":args.system_prompt_profile,"transport":"start_conversation.agent.system_prompt"}
            if args.completion_log_dir is not None:
                completion_log_dir=Path(args.completion_log_dir).expanduser().resolve(); completion_log_dir.mkdir(parents=True,exist_ok=True)
                executor += ["--completion-log-dir",str(completion_log_dir)]
                summary["completion_logging"]={"enabled":True,"directory":str(completion_log_dir)}
            executor=tuple(executor)
            vr=run_vertical(workspace=isolated.workspace,revision=revision,request_id="phase7-s4-openhands",task_id="phase7-trivial-edit",requester_ref="user://phase7-compatibility",authority_ref="authority://phase7-compatibility",acceptance_authority_ref="acceptance://phase7-independent-verifier",scope=("value.py",),candidate_files=("value.py",),affected_components=("fixture",),characterization_source_ref="evidence://phase7-s4-frozen-task",executor_argv=executor,verifier_argv=(sys.executable,"-c",'from pathlib import Path; ns={}; exec(Path("value.py").read_text(encoding="utf-8"),ns); ok=ns.get("VALUE")=="after"; print("VERIFIER_OK" if ok else "VERIFIER_BAD"); raise SystemExit(0 if ok else 9)'),evidence_dir=evidence/"vertical",max_wall_time_seconds=args.vertical_wall_time_seconds)
            vertical=vr.to_dict(); summary["vertical"]=vertical
            adapter=json.loads(result_path.read_text(encoding="utf-8")) if result_path.is_file() else {"error":{"type":"MissingAdapterEvidence","message":"OpenHands harness result missing"}}; summary["adapter"]=adapter
            obs=adapter.get("observations") if isinstance(adapter.get("observations"),dict) else {}
            run_root=Path(vr.evidence_root); patch_path=run_root/"workspace.patch"; patch_text=patch_path.read_text(encoding="utf-8",errors="replace") if patch_path.is_file() else ""
            patch_ok='-VALUE = "before"' in patch_text and '+VALUE = "after"' in patch_text
            verifier_path=run_root/"verification-summary.json"; verifier=json.loads(verifier_path.read_text(encoding="utf-8")) if verifier_path.is_file() else {}; verifier_ok=verifier.get("status")=="PASSED"
            usage=token_usage(adapter); summary["telemetry"]={**usage,"provider_api_cost_usd":0}
            final_state=isolated.capture_state().to_dict(); source_state=capture_repository_state(source).to_dict(); cleanup=isolated.remove(); isolated=None
            agent_info=(adapter.get("conversation_info") or {}).get("agent") if isinstance(adapter.get("conversation_info"),dict) else {}
            agent_context=agent_info.get("agent_context") if isinstance(agent_info,dict) and isinstance(agent_info.get("agent_context"),dict) else {}
            suffix=str(agent_context.get("system_message_suffix") or "")
            platform_contract_observed=(args.platform_contract is None) or ("<PLATFORM_CONTRACT>" in suffix and "Platform: Windows-native." in suffix and "Terminal tool shell: PowerShell." in suffix and (args.platform_contract != "windows-powershell-v2" or "Instruction precedence for this runtime:" in suffix))
            system_prompt=str(agent_info.get("system_prompt") or "") if isinstance(agent_info,dict) else ""
            event_items=((adapter.get("events") or {}).get("items") or []) if isinstance(adapter.get("events"),dict) else []
            system_prompt_events=[item for item in event_items if isinstance(item,dict) and item.get("kind")=="SystemPromptEvent"]
            event_system_prompt=""
            if system_prompt_events:
                event_prompt_obj=system_prompt_events[0].get("system_prompt")
                if isinstance(event_prompt_obj,dict): event_system_prompt=str(event_prompt_obj.get("text") or "")
            if args.system_prompt_profile is None:
                system_prompt_profile_observed=True
            elif args.system_prompt_profile=="windows-minimal-v1":
                system_prompt_profile_observed=("The platform contract in dynamic context is authoritative for shell syntax and path shape." in system_prompt and "The platform contract in dynamic context is authoritative for shell syntax and path shape." in event_system_prompt and "<SOUL>" not in event_system_prompt and "find, grep" not in event_system_prompt and "using sed and grep" not in event_system_prompt)
            elif args.system_prompt_profile=="windows-embedded-v1":
                embedded_markers=("Platform: Windows-native.","Terminal tool shell: PowerShell.","Use PowerShell-native commands such as Get-ChildItem and Get-Content.","Ignore generic tool text claiming absolute paths must start with '/'.")
                system_prompt_profile_observed=(all(marker in system_prompt for marker in embedded_markers) and all(marker in event_system_prompt for marker in embedded_markers) and "<SOUL>" not in event_system_prompt)
            else:
                system_prompt_profile_observed=False
            max_iterations_observed=(adapter.get("conversation_info") or {}).get("max_iterations")==args.max_iterations if isinstance(adapter.get("conversation_info"),dict) else False
            summary["gates"].update({"max_iterations_observed":max_iterations_observed,"explicit_local_binding":(adapter.get("llm_binding") or {}).get("base_url")==LLAMA_BASE and (adapter.get("llm_binding") or {}).get("model")==f"openai/{args.model_alias}","platform_contract_observed":platform_contract_observed,"system_prompt_profile_observed":system_prompt_profile_observed,"model_calls_observed":model_call_observed(adapter),"inspect_observed":obs.get("inspectObserved") is True,"command_observed":obs.get("commandObserved") is True,"event_edit_signal":obs.get("editObserved") is True,"edit_observed":len(vertical.get("changed_files") or [])>0,"termination_observed":str(adapter.get("execution_status") or "").lower() in {"finished","error","stuck","stopped"},"patch_captured":patch_ok,"independent_verifier":verifier_ok,"source_repository_unchanged":source_state.get("clean") is True,"workspace_cleanup":cleanup.removed})
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
