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
    parser.add_argument("--completion-log-dir")
    args = parser.parse_args()

    upstream = Path(args.upstream).resolve()
    bin_dir = upstream / "node_modules" / ".bin"
    vite_node = bin_dir / ("vite-node.cmd" if sys.platform.startswith("win") else "vite-node")
    if not vite_node.is_file():
        raise SystemExit(f"vite-node executable missing after exact npm install: {vite_node}")

    config_dir = upstream / ".tmp"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "codepro-phase7-vite-node.config.mts"
    config_path.write_text(
        """import { resolve } from "node:path";
import { defineConfig } from "vite";

const root = process.cwd();
export default defineConfig({
  define: {
    __EXTENSIONS_SKILLS_DIR__: JSON.stringify(
      resolve(root, "node_modules", "@openhands", "extensions", "skills"),
    ),
  },
  resolve: {
    alias: [{ find: /^#\\//, replacement: resolve(root, "src") + "/" }],
  },
  ssr: {
    noExternal: ["@openhands/typescript-client"],
  },
});
""",
        encoding="utf-8",
        newline="\n",
    )

    argv = [
        str(vite_node),
        "-c",
        str(config_path),
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
    if args.completion_log_dir:
        argv += ["--completion-log-dir", args.completion_log_dir]
    completed = subprocess.run(
        argv, cwd=upstream, capture_output=True, text=True,
        encoding="utf-8", errors="replace", shell=False, check=False, timeout=280
    )
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)
    return completed.returncode

if __name__ == "__main__":
    raise SystemExit(main())
