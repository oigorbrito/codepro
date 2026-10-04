#!/usr/bin/env python3
"""Read-only preflight for local Authenticode signing capability."""

from __future__ import annotations

import json
import subprocess


PS = r"""
$ErrorActionPreference = 'SilentlyContinue'

function Test-Chain($cert) {
  $chain = New-Object System.Security.Cryptography.X509Certificates.X509Chain
  $ok = $chain.Build($cert)
  [pscustomobject]@{
    ok = [bool]$ok
    status = @($chain.ChainStatus | ForEach-Object { $_.Status.ToString() })
  }
}

$stores = @('Cert:\CurrentUser\My', 'Cert:\LocalMachine\My')
$certs = foreach($store in $stores) {
  if(Test-Path $store) {
    Get-ChildItem $store | ForEach-Object {
      $c = $_
      $ekuOids = @($c.EnhancedKeyUsageList | ForEach-Object { $_.ObjectId.Value })
      if($ekuOids -contains '1.3.6.1.5.5.7.3.3') {
        $chain = Test-Chain $c
        [pscustomobject]@{
          store = $store
          thumbprint = $c.Thumbprint
          has_private_key = [bool]$c.HasPrivateKey
          not_before = $c.NotBefore.ToUniversalTime().ToString('o')
          not_after = $c.NotAfter.ToUniversalTime().ToString('o')
          chain_ok = [bool]$chain.ok
          chain_status = @($chain.status)
        }
      }
    }
  }
}

$signtool = Get-Command signtool.exe -ErrorAction SilentlyContinue
if(-not $signtool) {
  $candidates = Get-ChildItem 'C:\Program Files (x86)\Windows Kits\10\bin' -Filter signtool.exe -Recurse -File -ErrorAction SilentlyContinue |
    Sort-Object FullName -Descending
  $signtoolPaths = @($candidates | ForEach-Object { $_.FullName })
} else {
  $signtoolPaths = @($signtool.Source)
}

[pscustomobject]@{
  code_signing_certificates = @($certs)
  usable_code_signing_certificate_count = @($certs | Where-Object { $_.has_private_key -and $_.chain_ok -and ([datetime]$_.not_after -gt [datetime]::UtcNow) }).Count
  signtool_paths = @($signtoolPaths)
} | ConvertTo-Json -Depth 6 -Compress
"""

def main() -> int:
    p = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", PS],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    payload: dict[str, object] = {
        "schema_version": 1,
        "operation": "phase7q-authenticode-signing-capability-preflight",
        "modifies_files": False,
        "modifies_policy": False,
        "returncode": p.returncode,
        "stderr": p.stderr,
    }
    if p.stdout.strip():
        try:
            payload["result"] = json.loads(p.stdout)
        except json.JSONDecodeError:
            payload["raw_stdout"] = p.stdout
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if p.returncode == 0 else p.returncode

if __name__ == "__main__":
    raise SystemExit(main())
