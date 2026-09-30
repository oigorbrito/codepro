#!/usr/bin/env python3
"""Inspect identity and Authenticode state of frozen llama.cpp runtime files without modifying them."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

RUNTIME_DIR = Path(r"D:\projetos\codepro-mini-runtime\downloads\llama-b11205-bin-win-cuda-13.4-x64")
FILES = ("llama-server.exe", "llama-server-impl.dll")


def sha256(path: Path) -> str:
    d = hashlib.sha256()
    with path.open("rb") as h:
        for chunk in iter(lambda: h.read(1024 * 1024), b""):
            d.update(chunk)
    return d.hexdigest().upper()


def signature(path: Path) -> dict[str, object]:
    ps = (
        "$s=Get-AuthenticodeSignature -LiteralPath "
        + repr(str(path))
        + "; "
        + "[pscustomobject]@{Status=$s.Status.ToString();StatusMessage=$s.StatusMessage;"
        + "SignerSubject=if($s.SignerCertificate){$s.SignerCertificate.Subject}else{$null};"
        + "SignerThumbprint=if($s.SignerCertificate){$s.SignerCertificate.Thumbprint}else{$null};"
        + "TimeStamperSubject=if($s.TimeStamperCertificate){$s.TimeStamperCertificate.Subject}else{$null}}"
        + " | ConvertTo-Json -Compress"
    )
    p = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps],
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
    rows = []
    for name in FILES:
        path = (RUNTIME_DIR / name).resolve()
        row: dict[str, object] = {"path": str(path), "exists": path.is_file()}
        if path.is_file():
            row.update(
                {
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                    "authenticode": signature(path),
                    "zone_identifier_exists": Path(str(path) + ":Zone.Identifier").exists(),
                }
            )
        rows.append(row)
    print(
        json.dumps(
            {
                "schema_version": 1,
                "operation": "phase7q-frozen-runtime-signature-preflight",
                "modifies_files": False,
                "runtime_dir": str(RUNTIME_DIR),
                "files": rows,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
