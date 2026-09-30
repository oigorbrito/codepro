#!/usr/bin/env python3
"""Inspect Windows application-control posture without changing policy or files."""

from __future__ import annotations

import json
import subprocess


def run_ps(script: str) -> dict[str, object]:
    p = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    out: dict[str, object] = {"returncode": p.returncode, "stderr": p.stderr}
    if p.stdout.strip():
        try:
            out["result"] = json.loads(p.stdout)
        except json.JSONDecodeError:
            out["raw_stdout"] = p.stdout
    return out


def main() -> int:
    device_guard = run_ps(r"""
$dg = Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard -ErrorAction SilentlyContinue
$dg | Select-Object InstanceIdentifier,Version,VirtualizationBasedSecurityStatus,CodeIntegrityPolicyEnforcementStatus,UsermodeCodeIntegrityPolicyEnforcementStatus,SecurityServicesConfigured,SecurityServicesRunning,SecurityFeaturesEnabled,AvailableSecurityProperties,RequiredSecurityProperties | ConvertTo-Json -Depth 3 -Compress
""")
    ci_policies = run_ps(r"""
$paths = @(
  "$env:windir\System32\CodeIntegrity\CiPolicies\Active",
  "$env:windir\System32\CodeIntegrity"
)
$items = foreach($p in $paths) {
  if(Test-Path -LiteralPath $p) {
    Get-ChildItem -LiteralPath $p -Force -File -ErrorAction SilentlyContinue |
      Select-Object FullName,Name,Length,LastWriteTimeUtc
  }
}
$items | ConvertTo-Json -Depth 4 -Compress
""")
    registry = run_ps(r"""
$paths = @(
 'HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy',
 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard',
 'HKLM:\SOFTWARE\Microsoft\Windows Defender\SmartScreen'
)
$out = foreach($p in $paths) {
  if(Test-Path $p) {
    $item = Get-ItemProperty -Path $p
    $values = [ordered]@{}
    foreach($prop in $item.PSObject.Properties) {
      if($prop.Name -notlike 'PS*') {
        $values[$prop.Name] = $prop.Value
      }
    }
    [pscustomobject]@{Path=$p; Values=$values}
  }
}
$out | ConvertTo-Json -Depth 4 -Compress
""")
    payload = {
        "schema_version": 1,
        "operation": "phase7q-windows-application-control-posture",
        "policy_changes": False,
        "file_changes": False,
        "device_guard": device_guard,
        "code_integrity_policy_files": ci_policies,
        "registry": registry,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
