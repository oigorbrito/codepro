#!/usr/bin/env python3
"""Deterministic scaffold fixture for Phase 6 plumbing validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).parents[1].resolve()
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from arkx.repository_operations import RepositoryToolbox  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="src/value.txt")
    parser.add_argument("--scope", action="append", default=["src"])
    parser.add_argument("--expected-before", default="before\n")
    parser.add_argument("--replacement", default="after\n")
    args = parser.parse_args(argv)

    toolbox = RepositoryToolbox(Path.cwd(), authorized_scope=tuple(args.scope))
    observations = []

    inspected = toolbox.inspect(args.target)
    observations.append(inspected.to_dict())
    if inspected.stdout != args.expected_before:
        print(json.dumps(
            {"operations": observations, "failure": "INSPECT_MISMATCH"},
            sort_keys=True,
        ))
        return 10

    edited = toolbox.edit(args.target, args.replacement)
    observations.append(edited.to_dict())

    command = toolbox.command(
        (
            sys.executable,
            "-c",
            "from pathlib import Path; "
            "value=Path('src/value.txt').read_text(encoding='utf-8'); "
            "print('COMMAND_OK' if value == 'after\\n' else 'COMMAND_BAD'); "
            "raise SystemExit(0 if value == 'after\\n' else 7)",
        ),
        timeout_seconds=10,
    )
    observations.append(command.to_dict())

    payload = {
        "fixture": "PHASE6_CONTROLLED_SCAFFOLD",
        "operations": observations,
        "success": (
            command.exit_code == 0
            and not command.timed_out
            and command.stdout.strip() == "COMMAND_OK"
        ),
    }
    print(json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ))
    return 0 if payload["success"] else 11


if __name__ == "__main__":
    raise SystemExit(main())
