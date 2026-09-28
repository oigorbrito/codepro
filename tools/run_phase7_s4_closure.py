#!/usr/bin/env python3
"""Run S4, close Phase 7 classification, and stop at the post-Phase-7 gate review."""

from __future__ import annotations

import json, os, re, shutil, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).parents[1].resolve()
BRANCH="phase7/scaffold-compatibility"
EVIDENCE=ROOT/"evidence"/"phase7-scaffold-compatibility"/"S4-OpenHands"
DIAGNOSTICS=ROOT/"evidence"/"phase7-scaffold-compatibility"/"diagnostics"
MANIFEST=ROOT/"experiments"/"phase7"/"scaffold-pool.json"
AUDIT=ROOT/"docs"/"audits"/"phase7-s4-openhands-20260928.md"

def run(argv:list[str],*,env:dict[str,str]|None=None,check:bool=True,timeout:int|None=None)->subprocess.CompletedProcess[str]:
    p=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,text=True,encoding="utf-8",errors="replace",shell=False,check=False,timeout=timeout)
    if p.stdout: sys.stdout.write(p.stdout)
    if p.stderr: sys.stderr.write(p.stderr)
    if check and p.returncode!=0: raise RuntimeError(f"command failed ({p.returncode}): {argv!r}")
    return p

def git(*args:str,check:bool=True)->subprocess.CompletedProcess[str]: return run(["git",*args],check=check)

def archive_prior()->None:
    if not EVIDENCE.exists(): return
    summary=EVIDENCE/"s4-summary.json"; classification="INCOMPLETE"
    if summary.is_file():
        try: classification=str(json.loads(summary.read_text(encoding="utf-8")).get("classification") or "UNKNOWN")
        except Exception: classification="UNREADABLE"
    DIAGNOSTICS.mkdir(parents=True,exist_ok=True); attempt=len([x for x in DIAGNOSTICS.iterdir() if x.is_dir() and x.name.startswith("s4-attempt-")])+1
    label=re.sub(r"[^a-z0-9]+","-",classification.lower()).strip("-") or "unknown"
    while (DIAGNOSTICS/f"s4-attempt-{attempt}-{label}").exists(): attempt+=1
    dest=DIAGNOSTICS/f"s4-attempt-{attempt}-{label}"; shutil.move(str(EVIDENCE),str(dest)); print(f"PREVIOUS_S4_ATTEMPT_ARCHIVED = {dest}")

def update_manifest(summary:dict)->tuple[int,list[str]]:
    m=json.loads(MANIFEST.read_text(encoding="utf-8")); found=False
    for c in m.get("candidates",[]):
        if c.get("id")=="S4":
            found=True; c["phase7_status"]=summary["classification"]; c["evidence"]="evidence/phase7-scaffold-compatibility/S4-OpenHands/s4-summary.json"
            c["observed"]={"vertical_status":(summary.get("vertical") or {}).get("status"),"vertical_reason":(summary.get("vertical") or {}).get("reason"),"native_contract":summary.get("native_contract"),"agent_server_version":summary.get("agent_server_version"),"prompt_tokens":(summary.get("telemetry") or {}).get("prompt_tokens"),"completion_tokens":(summary.get("telemetry") or {}).get("completion_tokens"),"gates":summary.get("gates"),"blocker":summary.get("blocker")}
    if not found: raise RuntimeError("S4 candidate missing from manifest")
    statuses=[str(c.get("phase7_status")) for c in m.get("candidates",[])]
    survivors=sum(1 for s in statuses if s=="COMPATIBLE")
    MANIFEST.write_text(json.dumps(m,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n"); return survivors,statuses

def write_audit(summary:dict,survivors:int,statuses:list[str])->None:
    gates=summary.get("gates") or {}; tele=summary.get("telemetry") or {}; vert=summary.get("vertical") or {}
    lines=["# Phase 7 S4 - OpenHands compatibility audit","","Date: 2026-09-28","","## Frozen identity","","repository = OpenHands/OpenHands","agent_canvas_version = 1.21.0","commit = fc6d890f7b21c71a17de60d50597c00355e235ea","agent_server_version = 1.49.3","automation_version = 1.13.3","","## Native contract","","Agent Canvas request builder -> Agent Server 1.49.3 -> OpenHands agent tools -> isolated repository -> CodePro verifier","","The local LLM binding follows the upstream mock-LLM E2E contract: `openai/<model>` plus explicit `base_url`. The llama.cpp configuration is kept identical to S1/S2: no additional reasoning-mode override.","","## Result","",f"classification = {summary.get('classification')}",f"vertical_status = {vert.get('status')}",f"vertical_reason = {vert.get('reason')}",f"prompt_tokens = {tele.get('prompt_tokens')}",f"completion_tokens = {tele.get('completion_tokens')}",f"blocker = {summary.get('blocker')}","","## Gates",""]
    for k in sorted(gates): lines.append(f"{k.upper()} = {'PASS' if gates.get(k) is True else gates.get(k)}")
    lines += ["","## Phase 7 pool closure","",f"candidate_statuses = {statuses}",f"compatible_survivors = {survivors}","","All four frozen scaffold cells are now classified. This does not promote or select a scaffold. Phase 8 remains NOT_STARTED until a post-Phase-7 gate review decides whether the comparative scaffold screen is executable with the surviving pool.","","COMPATIBLE != SELECTED","EXECUTED != VERIFIED","VERIFIED != ACCEPTED","NO_SILENT_FALLBACK","NO_SILENT_EXECUTOR_SWITCH","","Evidence: evidence/phase7-scaffold-compatibility/S4-OpenHands/.",""]
    AUDIT.parent.mkdir(parents=True,exist_ok=True); AUDIT.write_text("\n".join(lines)+"\n",encoding="utf-8",newline="\n")

def update_roadmap(summary:dict,survivors:int)->None:
    p=ROOT/"roadmap.md"; text=p.read_text(encoding="utf-8"); a=text.index("## Phase 7"); b=text.index("## Phase 8"); block=text[a:b]
    if "- S4 OpenHands: **NEXT**." not in block: raise RuntimeError("S4 roadmap NEXT cell missing")
    block=block.replace("- S4 OpenHands: **NEXT**.",f"- S4 OpenHands: **{summary['classification']}** — docs/audits/phase7-s4-openhands-20260928.md.")
    old="""For each:

- [ ] Install and record version/commit.
- [ ] Connect to local runtime.
- [ ] Execute trivial repository task.
- [ ] Confirm inspect/edit/command/termination.
- [ ] Capture artifacts and telemetry.
- [ ] Verify patch.
- [ ] Classify compatibility."""
    new="""For each frozen candidate, execute the compatibility cell as far as the platform/scaffold permits and preserve blockers without substitution:

- [x] Attempt installation and record exact version/commit.
- [x] Attempt explicit local-runtime binding where installation/runtime startup is reachable.
- [x] Execute the frozen trivial repository task where the scaffold reaches execution.
- [x] Capture inspect/edit/command/termination observations where reachable; unknown remains unknown.
- [x] Capture artifacts and telemetry for every reached boundary.
- [x] Invoke the independent verifier only after an observable repository change.
- [x] Classify all four frozen candidates."""
    if old in block: block=block.replace(old,new)
    phase8_state="NEXT" if survivors>=1 else "BLOCKED_BY_NO_COMPATIBLE_SCAFFOLD"
    block=re.sub(r"\*\*Phase status:\*\* IN_PROGRESS[^\r\n]*",f"**Phase status:** COMPLETE — all four frozen scaffold cells classified; compatible survivors = {survivors}; Phase 8 = {phase8_state}.",block,count=1)
    text=text[:a]+block+text[b:]
    text=text.replace("PHASE 7   Scaffold compatibility        IN_PROGRESS","PHASE 7   Scaffold compatibility        COMPLETE")
    text=text.replace("STATUS = IN_PROGRESS / S4_NEXT","STATUS = COMPLETE / PR90_ACCEPTANCE_BEFORE_PHASE8")
    p.write_text(text,encoding="utf-8",newline="\n")

def repo_gates()->None:
    run([sys.executable,"tools/check_foundation.py"]); print("FOUNDATION = PASS")
    env=os.environ.copy(); env["PYTHONPATH"]=str(ROOT/"src"); run([sys.executable,"-m","unittest","discover","-s","tests","-t",".","-v"],env=env); print("PYTHON_TESTS = PASS")
    npm=shutil.which("npm.cmd") or shutil.which("npm");
    if not npm: raise RuntimeError("npm executable not found")
    run([npm,"run","lint"]); print("NPM_LINT = PASS"); run([npm,"run","build"]); print("NPM_BUILD = PASS")

def main()->int:
    print("======================================================"); print(" PHASE 7 - S4 OPENHANDS + PHASE 7 CLOSURE"); print("======================================================")
    git("fetch","origin"); local=git("show-ref","--verify","--quiet",f"refs/heads/{BRANCH}",check=False)
    git("switch",BRANCH) if local.returncode==0 else git("switch","-c",BRANCH,"--track",f"origin/{BRANCH}")
    git("pull","--ff-only","origin",BRANCH); archive_prior()
    env=os.environ.copy(); env["PYTHONPATH"]=str(ROOT/"src"); run([sys.executable,"tools/run_phase7_s4_openhands.py","--evidence-dir",str(EVIDENCE)],env=env,timeout=9000)
    sp=EVIDENCE/"s4-summary.json";
    if not sp.is_file(): raise RuntimeError("S4 summary missing")
    summary=json.loads(sp.read_text(encoding="utf-8")); classification=str(summary.get("classification") or "").strip()
    if not classification: raise RuntimeError("S4 classification missing")
    repo_gates(); survivors,statuses=update_manifest(summary); write_audit(summary,survivors,statuses); update_roadmap(summary,survivors)
    roadmap=(ROOT/"roadmap.md").read_text(encoding="utf-8")
    if "STATUS = COMPLETE / PR90_ACCEPTANCE_BEFORE_PHASE8" not in roadmap: raise RuntimeError("roadmap Phase 7 closure pointer missing")
    print("ROADMAP_SYNC = PASS")
    git("add","--","roadmap.md","experiments/phase7/scaffold-pool.json","docs/audits/phase7-s4-openhands-20260928.md","docs/audits/phase7-s3-autocoderover-20260928.md","evidence/phase7-scaffold-compatibility")
    staged=git("diff","--cached","--name-only").stdout.splitlines()
    if not staged: raise RuntimeError("no Phase 7 closure files staged")
    if any(x.lower().endswith(".gguf") for x in staged): raise RuntimeError("GGUF unexpectedly staged")
    authored=["roadmap.md","experiments/phase7/scaffold-pool.json","docs/audits/phase7-s4-openhands-20260928.md","docs/audits/phase7-s3-autocoderover-20260928.md","evidence/phase7-scaffold-compatibility/S4-OpenHands/s4-summary.json","evidence/phase7-scaffold-compatibility/S4-OpenHands/upstream-identity.json","evidence/phase7-scaffold-compatibility/S4-OpenHands/prerequisites.json"]
    existing=[x for x in authored if (ROOT/x).exists()]; git("diff","--cached","--check","--",*existing); print("AUTHORED_DIFF_CHECK = PASS")
    before=git("rev-parse","HEAD").stdout.strip(); git("commit","-m","phase7: classify S4 and close scaffold compatibility"); after=git("rev-parse","HEAD").stdout.strip()
    if after==before: raise RuntimeError("Phase 7 closure HEAD did not advance")
    git("push","origin",BRANCH); git("fetch","origin"); remote=git("rev-parse",f"origin/{BRANCH}").stdout.strip()
    if remote!=after: raise RuntimeError("remote Phase 7 HEAD mismatch")
    ahead=int(git("rev-list","--count",f"origin/main..origin/{BRANCH}").stdout.strip()); gates=summary.get("gates") or {}; tele=summary.get("telemetry") or {}; vert=summary.get("vertical") or {}
    print(""); print("======================================================"); print(" PHASE 7 - FINAL RESULT"); print("======================================================")
    print(f"S4_CLASSIFICATION       = {classification}"); print(f"S4_VERTICAL_STATUS      = {vert.get('status')}"); print(f"S4_PROMPT_TOKENS        = {tele.get('prompt_tokens')}"); print(f"S4_COMPLETION_TOKENS    = {tele.get('completion_tokens')}")
    print(f"AGENT_CANVAS_READY      = {gates.get('agent_canvas_ready')}"); print(f"LOCAL_RUNTIME_READY     = {gates.get('local_runtime_ready')}"); print(f"MODEL_CALLS_OBSERVED    = {gates.get('model_calls_observed')}"); print(f"INSPECT_OBSERVED        = {gates.get('inspect_observed')}"); print(f"EDIT_OBSERVED           = {gates.get('edit_observed')}"); print(f"COMMAND_OBSERVED        = {gates.get('command_observed')}"); print(f"INDEPENDENT_VERIFIER    = {gates.get('independent_verifier')}")
    phase8_state="NEXT" if survivors>=1 else "BLOCKED_BY_NO_COMPATIBLE_SCAFFOLD"
    print(f"COMPATIBLE_SURVIVORS    = {survivors}"); print(f"POOL_STATUS              = {', '.join(statuses)}"); print("FOUNDATION               = PASS"); print("PYTHON_TESTS             = PASS"); print("NPM_LINT                 = PASS"); print("NPM_BUILD                = PASS"); print("PHASE7                    = COMPLETE"); print(f"PHASE8                    = {phase8_state}"); print(f"COMMIT_SHA                = {after}"); print(f"REMOTE_HEAD               = {remote}"); print(f"COMMITS_AHEAD_MAIN        = {ahead}"); print("NEXT                       = REMOTE_REVIEW_THEN_PR90_ACCEPTANCE"); return 0

if __name__=="__main__": raise SystemExit(main())
