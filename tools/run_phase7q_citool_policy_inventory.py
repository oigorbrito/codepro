#!/usr/bin/env python3
"""Inventory active Code Integrity policies with CiTool without modifying policy state."""

from __future__ import annotations

import json
import subprocess


TARGET_POLICY_ID = "{0283AC0F-FFF1-49AE-ADA1-8A933130CAD6}"


def main() -> int:
    p = subprocess.run(
        ["CiTool.exe", "-lp", "-json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    payload: dict[str, object] = {
        "schema_version": 1,
        "operation": "phase7q-citool-policy-inventory",
        "policy_changes": False,
        "returncode": p.returncode,
        "returncode_hex": f"0x{p.returncode & 0xFFFFFFFF:08X}",
        "stderr": p.stderr,
        "target_policy_id": TARGET_POLICY_ID,
    }
    if (p.returncode & 0xFFFFFFFF) == 0x80070005:
        payload["failure_class"] = "BLOCKED_BY_PRIVILEGE"
        payload["failure_detail"] = "ACCESS_DENIED"
        payload["inventory_established"] = False
    if p.stdout.strip():
        try:
            raw = json.loads(p.stdout)
            policies = raw.get("Policies", []) if isinstance(raw, dict) else []
            target = []
            for row in policies:
                if not isinstance(row, dict):
                    continue
                policy_id = str(row.get("PolicyID", "")).upper()
                if policy_id == TARGET_POLICY_ID:
                    target.append(row)
            payload["target_policies"] = target
            payload["target_match_count"] = len(target)
            payload["active_enforced_policies"] = [
                {
                    key: row.get(key)
                    for key in (
                        "PolicyID",
                        "BasePolicyID",
                        "FriendlyName",
                        "Version",
                        "IsSystemPolicy",
                        "IsSignedPolicy",
                        "IsOnDisk",
                        "IsEnforced",
                        "IsAuthorized",
                    )
                    if key in row
                }
                for row in policies
                if isinstance(row, dict) and str(row.get("IsEnforced", "")).lower() == "true"
            ]
        except json.JSONDecodeError:
            payload["raw_stdout"] = p.stdout
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if p.returncode == 0 else p.returncode


if __name__ == "__main__":
    raise SystemExit(main())
