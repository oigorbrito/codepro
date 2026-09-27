#!/usr/bin/env python3
"""Independently review the persisted first-M1 evidence bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).parents[1].resolve()
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from arkx.acceptance import AcceptanceStatus
from arkx.m1_acceptance import persist_acceptance, review_m1_doctor_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", required=True, type=Path)
    args = parser.parse_args()

    try:
        decision = review_m1_doctor_json(args.evidence_root)
        acceptance_path = persist_acceptance(args.evidence_root, decision)
    except (OSError, ValueError, FileExistsError, json.JSONDecodeError) as exc:
        print(json.dumps({
            "classification": "BLOCKED_M1_ACCEPTANCE_REVIEW",
            "error": f"{type(exc).__name__}: {exc}",
            "promotion": "NOT_AUTHORIZED",
        }, sort_keys=True))
        return 2

    output = {
        "classification": (
            "M1_INDEPENDENT_ACCEPTED"
            if decision.status is AcceptanceStatus.ACCEPTED
            else "BLOCKED_M1_ACCEPTANCE_REVIEW"
        ),
        "acceptance": decision.to_dict(),
        "acceptance_evidence": str(acceptance_path),
        "promotion": "NOT_AUTHORIZED",
        "release": "NOT_AUTHORIZED",
    }
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if decision.status is AcceptanceStatus.ACCEPTED else 2


if __name__ == "__main__":
    raise SystemExit(main())
