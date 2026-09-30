#!/usr/bin/env python3
"""Inspect retained provenance for the frozen llama.cpp b11205 package without modifying files."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(r"D:\projetos\codepro-mini-runtime")
DOWNLOADS = ROOT / "downloads"
TARGET_DIR = DOWNLOADS / "llama-b11205-bin-win-cuda-13.4-x64"


def sha256(path: Path) -> str:
    d = hashlib.sha256()
    with path.open("rb") as h:
        for chunk in iter(lambda: h.read(1024 * 1024), b""):
            d.update(chunk)
    return d.hexdigest().upper()


def row(path: Path) -> dict[str, object]:
    item: dict[str, object] = {
        "path": str(path.resolve()),
        "name": path.name,
        "is_file": path.is_file(),
        "is_dir": path.is_dir(),
    }
    if path.is_file():
        item["bytes"] = path.stat().st_size
        if path.stat().st_size <= 8 * 1024 * 1024 * 1024:
            item["sha256"] = sha256(path)
        item["zone_identifier_exists"] = Path(str(path) + ":Zone.Identifier").exists()
    return item


def main() -> int:
    candidates = []
    if DOWNLOADS.exists():
        for path in sorted(DOWNLOADS.iterdir()):
            name = path.name.lower()
            if "b11205" in name or "llama" in name or path.resolve() == TARGET_DIR.resolve():
                candidates.append(row(path))
    target_files = []
    if TARGET_DIR.exists():
        for path in sorted(TARGET_DIR.iterdir()):
            target_files.append(row(path))
    print(json.dumps({
        "schema_version": 1,
        "operation": "phase7q-frozen-runtime-provenance-preflight",
        "modifies_files": False,
        "downloads_root": str(DOWNLOADS),
        "target_dir": str(TARGET_DIR),
        "download_candidates": candidates,
        "target_directory_entries": target_files,
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
