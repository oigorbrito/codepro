#!/usr/bin/env python3
"""Inventory Phase 4 model artifacts and retained local evidence without executing a model."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1].resolve()
RUNTIME_ROOT = Path(r"D:\projetos\codepro-mini-runtime")
MODEL_ROOT = RUNTIME_ROOT / "models" / "phase4"
EVIDENCE_ROOT = ROOT / "evidence" / "phase4-model-compatibility"
TERMS = ("nanbeige", "qwen", "granite", "swe-dev", "swedev")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def artifact_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if not MODEL_ROOT.exists():
        return rows
    for path in sorted(MODEL_ROOT.rglob("*.gguf")):
        name_lower = path.name.lower()
        hints = sorted({term for term in TERMS if term in name_lower})
        rows.append(
            {
                "path": str(path.resolve()),
                "name": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "candidate_hints": hints,
            }
        )
    return rows


def evidence_references() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if not EVIDENCE_ROOT.exists():
        return rows
    for path in sorted(EVIDENCE_ROOT.rglob("*")):
        if not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
            continue
        if path.suffix.lower() not in {".json", ".jsonl", ".txt", ".md", ".log", ".csv"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lower = text.lower()
        matched = sorted({term for term in TERMS if term in lower})
        if not matched:
            continue
        lines = text.splitlines()
        excerpts: list[dict[str, object]] = []
        for index, line in enumerate(lines, start=1):
            line_lower = line.lower()
            if any(term in line_lower for term in matched):
                excerpts.append({"line": index, "text": line[:1200]})
                if len(excerpts) >= 20:
                    break
        rows.append(
            {
                "path": str(path.resolve()),
                "matched_terms": matched,
                "excerpts": excerpts,
            }
        )
    return rows


def main() -> int:
    payload = {
        "schema_version": 1,
        "operation": "phase7q-model-artifact-preflight",
        "execution": "NONE",
        "model_invocation": False,
        "runtime_root": str(RUNTIME_ROOT),
        "model_root": str(MODEL_ROOT),
        "evidence_root": str(EVIDENCE_ROOT),
        "artifacts": artifact_rows(),
        "evidence_references": evidence_references(),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
