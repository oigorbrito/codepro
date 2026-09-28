#!/usr/bin/env python3
"""Launch the pinned Agent Canvas E2E request-builder harness from an isolated CodePro workspace."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).parents[1].resolve()
HARNESS = ROOT / "tools" / "phase7_openhands_native.mts"

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", required=True)
    parser.add_argument("--backend-url", required=True)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--llm-base-url", required=True)
    parser.add_argument("--model-alias", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--issue", required=True)
    args = parser.parse_args()

    upstream = Path(args.upstream).resolve()
    bin_dir = upstream / "node_modules" / ".bin"
    vite_node = bin_dir / ("vite-node.cmd" if sys.platform.startswith("win") else "vite-node")
    if not vite_node.is_file():
        raise SystemExit(f"vite-node executable missing after exact npm install: {vite_node}")

    argv = [
        str(vite_node),
        "-c",
        str(upstream / "tests" / "e2e" / "live-acp" / "vite-node.config.mts"),
        str(HARNESS),
        "--",
        "--backend-url", args.backend_url,
        "--api-key", args.api_key,
        "--working-dir", args.working_dir,
        "--llm-base-url", args.llm_base_url,
        "--model-alias", args.model_alias,
        "--result", args.result,
        "--issue", args.issue,
    ]
    completed = subprocess.run(
        argv, cwd=upstream, capture_output=True, text=True,
        encoding="utf-8", errors="replace", shell=False, check=False, timeout=280
    )
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)
    return completed.returncode

if __name__ == "__main__":
    raise SystemExit(main())
