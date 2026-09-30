#!/usr/bin/env python3
"""Consolidated read-only closure collector for Phase7Q ENV-R1.

This script does not execute candidate binaries, invoke a model, replace a runtime,
or modify Windows policy. It independently reads the already-recorded Code Integrity
window through Get-WinEvent and wevtutil, then re-verifies the critical candidate
member identity and Authenticode state.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path


START_UTC = "2026-09-30T19:46:40.000Z"
END_UTC = "2026-09-30T19:47:30.000Z"
POLICY_ID = "0283ac0f-fff1-49ae-ada1-8a933130cad6"
RUNTIME_ROOT = Path(r"D:\projetos\codepro-mini-runtime")
CANDIDATE_DIR = RUNTIME_ROOT / "downloads" / "phase7q-remediation" / "b11295" / "extracted"
SERVER = CANDIDATE_DIR / "llama-server.exe"
SERVER_IMPL = CANDIDATE_DIR / "llama-server-impl.dll"
NEEDLES = [
    str(CANDIDATE_DIR).lower(),
    "llama-server.exe",
    "llama-server-impl.dll",
    "b11295",
]


def run(cmd: list[str]) -> dict[str, object]:
    p = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {
        "cmd": cmd,
        "returncode": p.returncode,
        "returncode_hex": f"0x{p.returncode & 0xFFFFFFFF:08X}",
        "stdout": p.stdout,
        "stderr": p.stderr,
    }


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def authenticode(path: Path) -> dict[str, object]:
    ps = (
        "$s=Get-AuthenticodeSignature -LiteralPath "
        + json.dumps(str(path))
        + "; [pscustomobject]@{Status=$s.Status.ToString();"
          "SignerSubject=if($s.SignerCertificate){$s.SignerCertificate.Subject}else{$null};"
          "SignerThumbprint=if($s.SignerCertificate){$s.SignerCertificate.Thumbprint}else{$null}}"
          " | ConvertTo-Json -Compress"
    )
    out = run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps])
    result: dict[str, object] = {
        "returncode": out["returncode"],
        "stderr": out["stderr"],
    }
    stdout = str(out["stdout"]).strip()
    if stdout:
        try:
            result["result"] = json.loads(stdout)
        except json.JSONDecodeError:
            result["raw_stdout"] = stdout
    return result


def get_winevent_capture() -> dict[str, object]:
    needles_ps = ",".join(json.dumps(x) for x in NEEDLES)
    ps = rf"""
$start=[datetime]::Parse({json.dumps(START_UTC)})
$end=[datetime]::Parse({json.dumps(END_UTC)})
$needles=@({needles_ps})
$events = Get-WinEvent -FilterHashtable @{{
  LogName='Microsoft-Windows-CodeIntegrity/Operational'
  StartTime=$start
  EndTime=$end
}} -ErrorAction Stop |
  Where-Object {{
    if ($_.Id -notin 3033,3076,3077) {{ return $false }}
    $m = $_.Message
    $xml = $_.ToXml()
    foreach ($needle in $needles) {{
      if (($m -and $m.ToLowerInvariant().Contains($needle.ToLowerInvariant())) -or
          ($xml -and $xml.ToLowerInvariant().Contains($needle.ToLowerInvariant()))) {{
        return $true
      }}
    }}
    return $false
  }} |
  ForEach-Object {{
    [pscustomobject]@{{
      TimeCreated = $_.TimeCreated.ToUniversalTime().ToString('o')
      Id = $_.Id
      Message = $_.Message
      Xml = $_.ToXml()
    }}
  }}
@($events) | ConvertTo-Json -Depth 6 -Compress
"""
    out = run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps])
    result: dict[str, object] = {
        "returncode": out["returncode"],
        "stderr": out["stderr"],
    }
    stdout = str(out["stdout"]).strip()
    if stdout:
        try:
            result["events"] = json.loads(stdout)
        except json.JSONDecodeError:
            result["raw_stdout"] = stdout
    return result


def wevtutil_capture() -> dict[str, object]:
    query = (
        "*[System["
        "(EventID=3033 or EventID=3076 or EventID=3077) and "
        f"TimeCreated[@SystemTime>='{START_UTC}' and @SystemTime<='{END_UTC}']"
        "]]"
    )
    out = run([
        "wevtutil.exe",
        "qe",
        "Microsoft-Windows-CodeIntegrity/Operational",
        f"/q:{query}",
        "/f:xml",
        "/e:Events",
    ])
    result: dict[str, object] = {
        "returncode": out["returncode"],
        "stderr": out["stderr"],
    }
    raw = str(out["stdout"])
    matched: list[dict[str, object]] = []
    if raw.strip():
        try:
            root = ET.fromstring(raw)
            ns = {"e": "http://schemas.microsoft.com/win/2004/08/events/event"}
            for event in root.findall("e:Event", ns):
                xml_text = ET.tostring(event, encoding="unicode")
                low = xml_text.lower()
                if not any(n in low for n in NEEDLES):
                    continue
                event_id = event.findtext("e:System/e:EventID", default="", namespaces=ns)
                time_node = event.find("e:System/e:TimeCreated", ns)
                system_time = time_node.attrib.get("SystemTime") if time_node is not None else None
                data: dict[str, list[str]] = {}
                for node in event.findall("e:EventData/e:Data", ns):
                    key = node.attrib.get("Name", "")
                    data.setdefault(key, []).append(node.text or "")
                matched.append({
                    "event_id": int(event_id) if event_id.isdigit() else event_id,
                    "system_time": system_time,
                    "event_data": data,
                    "xml": xml_text,
                })
            result["events"] = matched
        except ET.ParseError as exc:
            result["parse_error"] = str(exc)
            result["raw_stdout"] = raw
    return result


def extract_attribution(events: list[dict[str, object]]) -> dict[str, object]:
    blob = json.dumps(events, ensure_ascii=False).lower()
    return {
        "event_count": len(events),
        "candidate_path_observed": str(CANDIDATE_DIR).lower() in blob or "b11295" in blob,
        "server_exe_observed": "llama-server.exe" in blob,
        "server_impl_observed": "llama-server-impl.dll" in blob,
        "target_policy_id_observed": POLICY_ID.lower() in blob,
        "event_3033_observed": any(str(e.get("event_id", e.get("Id", ""))) == "3033" for e in events),
        "event_3076_observed": any(str(e.get("event_id", e.get("Id", ""))) == "3076" for e in events),
        "event_3077_observed": any(str(e.get("event_id", e.get("Id", ""))) == "3077" for e in events),
    }


def normalize_events(capture: dict[str, object]) -> list[dict[str, object]]:
    events = capture.get("events", [])
    if isinstance(events, dict):
        return [events]
    if isinstance(events, list):
        return [e for e in events if isinstance(e, dict)]
    return []


def main() -> int:
    primary = get_winevent_capture()
    independent = wevtutil_capture()

    primary_events = normalize_events(primary)
    independent_events = normalize_events(independent)

    payload = {
        "schema_version": 1,
        "operation": "phase7q-b11295-r1-closure-collector",
        "candidate_cell": "PHASE7Q-ENV-R1",
        "candidate_execution": False,
        "model_invocation": False,
        "runtime_replacement": False,
        "policy_changes": False,
        "file_changes": False,
        "window": {"start_utc": START_UTC, "end_utc": END_UTC},
        "critical_members": {
            "llama-server.exe": {
                "path": str(SERVER),
                "exists": SERVER.is_file(),
                "bytes": SERVER.stat().st_size if SERVER.is_file() else None,
                "sha256": sha256_file(SERVER),
                "authenticode": authenticode(SERVER),
            },
            "llama-server-impl.dll": {
                "path": str(SERVER_IMPL),
                "exists": SERVER_IMPL.is_file(),
                "bytes": SERVER_IMPL.stat().st_size if SERVER_IMPL.is_file() else None,
                "sha256": sha256_file(SERVER_IMPL),
                "authenticode": authenticode(SERVER_IMPL),
            },
        },
        "get_winevent": primary,
        "get_winevent_attribution": extract_attribution(primary_events),
        "wevtutil": independent,
        "wevtutil_attribution": extract_attribution(independent_events),
    }

    p_attr = payload["get_winevent_attribution"]
    i_attr = payload["wevtutil_attribution"]
    assert isinstance(p_attr, dict)
    assert isinstance(i_attr, dict)
    payload["independent_agreement"] = {
        "candidate_path": bool(p_attr["candidate_path_observed"] and i_attr["candidate_path_observed"]),
        "server_impl": bool(p_attr["server_impl_observed"] and i_attr["server_impl_observed"]),
        "target_policy_id": bool(p_attr["target_policy_id_observed"] and i_attr["target_policy_id_observed"]),
        "event_3077": bool(p_attr["event_3077_observed"] and i_attr["event_3077_observed"]),
    }

    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
