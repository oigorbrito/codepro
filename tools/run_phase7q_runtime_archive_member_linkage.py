#!/usr/bin/env python3
"""Compare retained b11205 ZIP members against current extracted runtime files without modifying anything."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(r"D:\projetos\codepro-mini-runtime\downloads")
ARCHIVE = ROOT / "llama-b11205-bin-win-cuda-13.4-x64.zip"
EXTRACTED = ROOT / "llama-b11205-bin-win-cuda-13.4-x64"
TARGETS = ("llama-server.exe", "llama-server-impl.dll")


def sha256_file(path: Path) -> str:
    d = hashlib.sha256()
    with path.open("rb") as h:
        for chunk in iter(lambda: h.read(1024 * 1024), b""):
            d.update(chunk)
    return d.hexdigest().upper()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def main() -> int:
    payload: dict[str, object] = {
        "schema_version": 1,
        "operation": "phase7q-runtime-archive-member-linkage",
        "modifies_files": False,
        "archive": str(ARCHIVE),
        "archive_exists": ARCHIVE.is_file(),
        "extracted_dir": str(EXTRACTED),
        "targets": [],
    }
    if not ARCHIVE.is_file():
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    payload["archive_sha256"] = sha256_file(ARCHIVE)
    with ZipFile(ARCHIVE, "r") as zf:
        names = zf.namelist()
        rows = []
        for target in TARGETS:
            matches = [name for name in names if Path(name).name.lower() == target.lower()]
            extracted = EXTRACTED / target
            row: dict[str, object] = {
                "target": target,
                "zip_matches": matches,
                "extracted_exists": extracted.is_file(),
            }
            if len(matches) == 1:
                data = zf.read(matches[0])
                row["zip_member"] = matches[0]
                row["zip_member_bytes"] = len(data)
                row["zip_member_sha256"] = sha256_bytes(data)
            if extracted.is_file():
                row["extracted_bytes"] = extracted.stat().st_size
                row["extracted_sha256"] = sha256_file(extracted)
            row["byte_identity_match"] = (
                row.get("zip_member_sha256") is not None
                and row.get("zip_member_sha256") == row.get("extracted_sha256")
            )
            rows.append(row)
    payload["targets"] = rows
    payload["all_targets_match"] = all(bool(row.get("byte_identity_match")) for row in rows)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload["all_targets_match"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
