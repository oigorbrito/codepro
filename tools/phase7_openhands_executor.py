#!/usr/bin/env python3
"""Launch the pinned Agent Canvas E2E request-builder harness from an isolated CodePro workspace."""

from __future__ import annotations

import argparse
import json
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
    parser.add_argument("--poll-timeout-seconds", type=int, default=240)
    parser.add_argument("--process-timeout-seconds", type=int, default=280)
    parser.add_argument("--platform-contract")
    parser.add_argument("--system-prompt-profile")
    parser.add_argument("--conversation-worktree", choices=("true", "false"), default="true")
    parser.add_argument("--cleanup-untracked-python-bytecode", choices=("true", "false"), default="false")
    parser.add_argument("--max-iterations", type=int, default=8)
    args = parser.parse_args()
    if args.poll_timeout_seconds < 1:
        raise SystemExit("--poll-timeout-seconds must be >= 1")
    if args.process_timeout_seconds <= args.poll_timeout_seconds:
        raise SystemExit("--process-timeout-seconds must be greater than --poll-timeout-seconds")
    if args.max_iterations < 1:
        raise SystemExit("--max-iterations must be >= 1")

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
        "--poll-timeout-seconds", str(args.poll_timeout_seconds),
        "--conversation-worktree", args.conversation_worktree,
        "--max-iterations", str(args.max_iterations),
    ]
    if args.completion_log_dir:
        argv += ["--completion-log-dir", args.completion_log_dir]
    if args.platform_contract:
        argv += ["--platform-contract", args.platform_contract]
    if args.system_prompt_profile:
        argv += ["--system-prompt-profile", args.system_prompt_profile]
    completed = subprocess.run(
        argv, cwd=upstream, capture_output=True, text=True,
        encoding="utf-8", errors="replace", shell=False, check=False, timeout=args.process_timeout_seconds
    )
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)

    cleanup_removed: list[str] = []
    if args.cleanup_untracked_python_bytecode == "true":
        working_dir = Path(args.working_dir).resolve()
        status = subprocess.run(
            ["git", "-C", str(working_dir), "status", "--porcelain=v1", "--untracked-files=all"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            shell=False, check=False, timeout=30,
        )
        if status.returncode != 0:
            raise SystemExit(f"unable to inspect workspace for ephemeral bytecode cleanup: {status.stderr.strip()}")
        for line in status.stdout.splitlines():
            if not line.startswith("?? "):
                continue
            rel = line[3:].strip().replace("\\", "/")
            parts = Path(rel).parts
            if "__pycache__" not in parts or not rel.endswith(".pyc"):
                continue
            candidate = (working_dir / rel).resolve()
            try:
                candidate.relative_to(working_dir)
            except ValueError:
                raise SystemExit(f"refusing bytecode cleanup outside workspace: {candidate}")
            if candidate.is_file():
                candidate.unlink()
                cleanup_removed.append(rel)
        result_path = Path(args.result).resolve()
        if result_path.is_file():
            payload = json.loads(result_path.read_text(encoding="utf-8"))
            payload["workspace_ephemeral_cleanup"] = {
                "policy": "untracked-python-bytecode-only-v1",
                "removed": sorted(cleanup_removed),
            }
            result_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        print("CODEPRO_EPHEMERAL_CLEANUP=" + json.dumps(sorted(cleanup_removed)))

    return completed.returncode

if __name__ == "__main__":
    raise SystemExit(main())
