#!/usr/bin/env python3
"""Diagnose Windows Application Control blocks relevant to Phase 7Q without changing policy."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone

CHANNEL = "Microsoft-Windows-CodeIntegrity/Operational"
EVENT_IDS = (3033, 3076, 3077)


def main() -> int:
    since = (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat()
    ps = rf"""
$start = [DateTime]::Parse('{since}').ToLocalTime()
$events = Get-WinEvent -FilterHashtable @{{LogName='{CHANNEL}'; StartTime=$start}} -ErrorAction SilentlyContinue |
  Where-Object {{ $_.Id -in {','.join(str(x) for x in EVENT_IDS)} }} |
  Select-Object -First 100 TimeCreated, Id, LevelDisplayName, Message, RecordId
$events | ConvertTo-Json -Depth 4 -Compress
"""
    proc = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    payload = {
        "schema_version": 1,
        "operation": "phase7q-windows-application-control-diagnostic",
        "policy_changes": False,
        "channel": CHANNEL,
        "event_ids": list(EVENT_IDS),
        "powershell_returncode": proc.returncode,
        "stderr": proc.stderr,
        "events": [],
    }
    if proc.stdout.strip():
        try:
            value = json.loads(proc.stdout)
            payload["events"] = value if isinstance(value, list) else [value]
        except json.JSONDecodeError:
            payload["raw_stdout"] = proc.stdout
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if proc.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
