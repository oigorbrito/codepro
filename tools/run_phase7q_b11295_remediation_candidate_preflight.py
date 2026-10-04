#!/usr/bin/env python3
"""Stage and inspect the exact Phase7Q b11295 remediation candidate.

This script downloads and extracts the candidate into an isolated directory.
It does not execute candidate binaries, replace the frozen runtime, or modify policy.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path


RUNTIME_ROOT = Path(r"D:\projetos\codepro-mini-runtime")
STAGING_ROOT = RUNTIME_ROOT / "downloads" / "phase7q-remediation" / "b11295"
ARCHIVE = STAGING_ROOT / "llama-b11295-bin-win-cuda-13.4-x64.zip"
EXTRACT_DIR = STAGING_ROOT / "extracted"
URL = "https://github.com/ggml-org/llama.cpp/releases/download/b11295/llama-b11295-bin-win-cuda-13.4-x64.zip"
EXPECTED_SHA256 = "5F2EC28C4DED2986499D6B7B9DBD1FECB6EE7182208F3167C40E8EE3D585D1DC"


def sha256_file(path: Path) -> str:
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
          "StatusMessage=$s.StatusMessage;"
          "SignerSubject=if($s.SignerCertificate){$s.SignerCertificate.Subject}else{$null};"
          "SignerThumbprint=if($s.SignerCertificate){$s.SignerCertificate.Thumbprint}else{$null}}"
          " | ConvertTo-Json -Compress"
    )
    p = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    result: dict[str, object] = {
        "returncode": p.returncode,
        "stderr": p.stderr,
    }
    if p.stdout.strip():
        try:
            result["result"] = json.loads(p.stdout)
        except json.JSONDecodeError:
            result["raw_stdout"] = p.stdout
    return result


def main() -> int:
    STAGING_ROOT.mkdir(parents=True, exist_ok=True)

    if not ARCHIVE.exists():
        p = subprocess.run(
            ["curl.exe", "-L", "--fail", "--output", str(ARCHIVE), URL],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if p.returncode != 0:
            print(json.dumps({
                "schema_version": 1,
                "operation": "phase7q-b11295-remediation-candidate-preflight",
                "download_returncode": p.returncode,
                "download_stderr": p.stderr,
                "policy_changes": False,
                "runtime_replacement": False,
                "candidate_execution": False,
            }, ensure_ascii=False, indent=2, sort_keys=True))
            return p.returncode

    archive_sha = sha256_file(ARCHIVE)
    digest_match = archive_sha == EXPECTED_SHA256

    if EXTRACT_DIR.exists():
        shutil.rmtree(EXTRACT_DIR)
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

    members: list[dict[str, object]] = []
    if digest_match:
        with zipfile.ZipFile(ARCHIVE) as zf:
            zf.extractall(EXTRACT_DIR)

        for path in sorted(EXTRACT_DIR.rglob("*")):
            if not path.is_file():
                continue
            row: dict[str, object] = {
                "relative_path": str(path.relative_to(EXTRACT_DIR)),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            if path.suffix.lower() in {".exe", ".dll"}:
                row["authenticode"] = authenticode(path)
            members.append(row)

    payload = {
        "schema_version": 1,
        "operation": "phase7q-b11295-remediation-candidate-preflight",
        "candidate_cell": "PHASE7Q-ENV-R1",
        "candidate_tag": "b11295",
        "candidate_commit": "3b3d022b823abaa62a467b26a44e10659e080ee7",
        "archive": str(ARCHIVE),
        "archive_bytes": ARCHIVE.stat().st_size if ARCHIVE.exists() else None,
        "archive_sha256": archive_sha if ARCHIVE.exists() else None,
        "expected_archive_sha256": EXPECTED_SHA256,
        "archive_digest_match": digest_match,
        "extract_dir": str(EXTRACT_DIR),
        "members": members,
        "policy_changes": False,
        "runtime_replacement": False,
        "candidate_execution": False,
        "modifies_files": True,
        "modification_scope": "isolated remediation staging directory only",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if digest_match else 2


if __name__ == "__main__":
    raise SystemExit(main())
