#!/usr/bin/env python3
"""Read-only broad Code Integrity capture for the Phase7Q b11295 R1 window."""

from __future__ import annotations

import json
import subprocess


START_UTC = "2026-09-30T19:46:40Z"
END_UTC = "2026-09-30T19:47:30Z"
CANDIDATE_DIR = r"D:\projetos\codepro-mini-runtime\downloads\phase7q-remediation\b11295\extracted"
NEEDLES = [
    "llama-server.exe",
    "llama-server-impl.dll",
    "b11295",
    CANDIDATE_DIR,
]


def main() -> int:
    needles_ps = ",".join(json.dumps(x) for x in NEEDLES)
    ps = rf"""
$start=[datetime]::Parse({json.dumps(START_UTC)})
$end=[datetime]::Parse({json.dumps(END_UTC)})
$needles=@({needles_ps})
$events = Get-WinEvent -FilterHashtable @{{
  LogName='Microsoft-Windows-CodeIntegrity/Operational'
  StartTime=$start
  EndTime=$end
}} -ErrorAction SilentlyContinue |
  Where-Object {{
    $_.Id -in 3033,3076,3077 -and (
      $m=$_.Message
      ($needles | Where-Object {{ $m -like ('*' + $_ + '*') }}).Count -gt 0
    )
  }} |
  Select-Object TimeCreated,Id,LevelDisplayName,Message
@($events) | ConvertTo-Json -Depth 6 -Compress
"""
    p = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    payload: dict[str, object] = {
        "schema_version": 1,
        "operation": "phase7q-b11295-broad-code-integrity-capture",
        "policy_changes": False,
        "file_changes": False,
        "candidate_execution": False,
        "start_utc": START_UTC,
        "end_utc": END_UTC,
        "needles": NEEDLES,
        "returncode": p.returncode,
        "stderr": p.stderr,
    }
    if p.stdout.strip():
        try:
            payload["events"] = json.loads(p.stdout)
        except json.JSONDecodeError:
            payload["raw_stdout"] = p.stdout
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if p.returncode == 0 else p.returncode


if __name__ == "__main__":
    raise SystemExit(main())
