#!/usr/bin/env python3
"""Execute the isolated b11295 candidate minimally and capture Code Integrity evidence.

This does not replace the frozen runtime, invoke a model, or modify policy.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path


RUNTIME_ROOT = Path(r"D:\projetos\codepro-mini-runtime")
CANDIDATE_DIR = RUNTIME_ROOT / "downloads" / "phase7q-remediation" / "b11295" / "extracted"
SERVER = CANDIDATE_DIR / "llama-server.exe"


def ps_json(command: str) -> dict[str, object]:
    p = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    out: dict[str, object] = {
        "returncode": p.returncode,
        "stderr": p.stderr,
    }
    if p.stdout.strip():
        try:
            out["result"] = json.loads(p.stdout)
        except json.JSONDecodeError:
            out["raw_stdout"] = p.stdout
    return out


def main() -> int:
    started = dt.datetime.now(dt.timezone.utc)
    zone = ps_json(
        "$p=" + json.dumps(str(SERVER)) + "; "
        "$z=Get-Item -LiteralPath $p -Stream Zone.Identifier -ErrorAction SilentlyContinue; "
        "[pscustomobject]@{Present=[bool]$z;Length=if($z){$z.Length}else{$null}} | ConvertTo-Json -Compress"
    )

    p = subprocess.run(
        [str(SERVER), "--version"],
        cwd=str(CANDIDATE_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    finished = dt.datetime.now(dt.timezone.utc)

    start_iso = started.astimezone().isoformat()
    ps_events = rf"""
$start = [datetime]::Parse({json.dumps(start_iso)})
$exe = {json.dumps(str(SERVER))}
$dir = {json.dumps(str(CANDIDATE_DIR))}
$events = Get-WinEvent -FilterHashtable @{{
  LogName='Microsoft-Windows-CodeIntegrity/Operational'
  StartTime=$start.AddSeconds(-5)
}} -ErrorAction SilentlyContinue |
  Where-Object {{
    $_.Id -in 3033,3076,3077 -and
    ($_.Message -like ('*' + $exe + '*') -or $_.Message -like ('*' + $dir + '*'))
  }} |
  Select-Object TimeCreated,Id,LevelDisplayName,Message
@($events) | ConvertTo-Json -Depth 5 -Compress
"""
    events = ps_json(ps_events)

    payload = {
        "schema_version": 1,
        "operation": "phase7q-b11295-isolated-execution-preflight",
        "candidate_cell": "PHASE7Q-ENV-R1",
        "candidate_execution": True,
        "model_invocation": False,
        "runtime_replacement": False,
        "policy_changes": False,
        "server": str(SERVER),
        "zone_identifier": zone,
        "started_utc": started.isoformat(),
        "finished_utc": finished.isoformat(),
        "process": {
            "argv": [str(SERVER), "--version"],
            "returncode": p.returncode,
            "returncode_hex": f"0x{p.returncode & 0xFFFFFFFF:08X}",
            "stdout": p.stdout,
            "stderr": p.stderr,
        },
        "code_integrity_events": events,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
