#!/usr/bin/env python3
"""Read-only diagnostics for elevation state and direct CiTool policy listing."""

from __future__ import annotations

import json
import subprocess


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


def main() -> int:
    whoami = run(["whoami", "/groups"])
    citool_help = run(["CiTool.exe", "-h"])
    citool_list = run(["CiTool.exe", "-lp", "-json"])
    groups_text = str(whoami.get("stdout", ""))
    high_integrity = ("S-1-16-12288" in groups_text) or ("High Mandatory Level" in groups_text) or ("Nível Obrigatório Alto" in groups_text)
    admin_deny_only = ("S-1-5-32-544" in groups_text) and (
        "deny only" in groups_text.lower() or "usado apenas para negar" in groups_text.lower()
    )
    payload = {
        "schema_version": 1,
        "operation": "phase7q-elevation-and-direct-citool-diagnostic",
        "policy_changes": False,
        "file_changes": False,
        "integrity_level_high": high_integrity,
        "administrators_group_deny_only": admin_deny_only,
        "effective_elevation": bool(high_integrity and not admin_deny_only),
        "whoami_groups": whoami,
        "citool_help": citool_help,
        "citool_list_policies": citool_list,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
