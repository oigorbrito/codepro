#!/usr/bin/env python3
"""Headless native AutoCodeRover task runner for Phase 7 S3."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from openai import OpenAI

from app import globals as acr_globals
from app import inference
from app.api.manage import ProjectApiManager
from app.model import common
from app.model.gpt import OpenaiModel
from app.post_process import get_final_patch_path
from app.task import PlainTask


class LocalOpenAIModel(OpenaiModel):
    """Bind the upstream OpenAI tool-call surface to one explicit local endpoint."""

    _instances = {}

    def __new__(cls, model_name: str, base_url: str):
        return object.__new__(cls)

    def __init__(self, model_name: str, base_url: str):
        if getattr(self, "_initialized", False):
            return
        self._phase7_base_url = base_url
        super().__init__(
            model_name,
            max_output_token=768,
            cost_per_input=0.0,
            cost_per_output=0.0,
            parallel_tool_call=False,
        )

    def setup(self) -> None:
        self.client = OpenAI(api_key="local-llm", base_url=self._phase7_base_url)

    def check_api_key(self) -> str:
        return "local-llm"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--issue", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--result", required=True)
    args = parser.parse_args(argv)

    workspace = Path(args.workspace).resolve()
    output_dir = Path(args.output_dir).resolve()
    result_path = Path(args.result).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "adapter": "autocoderover-native-local-issue",
        "workspace": str(workspace),
        "revision": args.revision,
        "model": args.model,
        "base_url": args.base_url,
        "model_call_surface": "upstream OpenaiModel.call with native ACR tool calls",
        "run_ok": False,
        "patch_path": None,
        "patch_applied": False,
        "tool_calls": [],
        "stats": None,
        "error": None,
    }

    try:
        model = LocalOpenAIModel(args.model, args.base_url)
        model.setup()
        observed_base = str(model.client.base_url).rstrip("/") if model.client else ""
        if observed_base != args.base_url.rstrip("/"):
            raise RuntimeError(f"local model base_url mismatch: {observed_base!r}")

        common.SELECTED_MODEL = model
        common.MODEL_TEMP = 0.0
        common.thread_cost.process_cost = 0.0
        common.thread_cost.process_input_tokens = 0
        common.thread_cost.process_output_tokens = 0

        acr_globals.output_dir = str(output_dir)
        acr_globals.conv_round_limit = 4
        acr_globals.enable_sbfl = False
        acr_globals.enable_layered = False
        acr_globals.enable_validation = False
        acr_globals.enable_angelic = False
        acr_globals.enable_perfect_angelic = False
        acr_globals.only_save_sbfl_result = False
        acr_globals.disable_patch_generation = False

        task = PlainTask(
            commit_hash=args.revision,
            local_path=str(workspace),
            problem_statement=args.issue,
        )
        manager = ProjectApiManager(task, str(output_dir))
        run_ok = inference.run_one_task(
            str(output_dir),
            manager,
            args.issue,
        )
        manager.dump_tool_call_sequence_to_file()
        manager.dump_tool_call_layers_to_file()
        payload["run_ok"] = bool(run_ok)
        payload["tool_calls"] = manager.tool_call_sequence
        payload["stats"] = model.get_overall_exec_stats()

        final_patch = get_final_patch_path(str(output_dir))
        if final_patch:
            patch = Path(final_patch).resolve()
            payload["patch_path"] = str(patch)
            applied = subprocess.run(
                ["git", "-C", str(workspace), "apply", "--whitespace=nowarn", str(patch)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                shell=False,
                check=False,
                timeout=30,
            )
            payload["patch_apply"] = {
                "returncode": applied.returncode,
                "stdout": applied.stdout,
                "stderr": applied.stderr,
            }
            payload["patch_applied"] = applied.returncode == 0

    except Exception as exc:
        payload["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }

    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
