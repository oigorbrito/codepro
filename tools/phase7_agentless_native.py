#!/usr/bin/env python3
"""Native Agentless repair adapter for one bounded Phase 7 compatibility task."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from pathlib import Path
import sys

from agentless.repair.repair import (
    _post_process_multifile_repair,
    repair_prompt_combine_topn,
    repair_relevant_file_instruction,
)
from agentless.util.model import make_model


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    parser.add_argument("--issue", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    target = Path(args.target)
    output = Path(args.output)
    logger = logging.getLogger("phase7-agentless")
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler(sys.stderr))

    payload = {
        "adapter": "agentless-native-repair",
        "target": args.target,
        "model": args.model,
        "inspect_observed": False,
        "model_call_observed": False,
        "termination_observed": False,
        "edit_parser_observed": False,
        "edit_applied": False,
        "raw_response": None,
        "usage": None,
        "error": None,
    }

    try:
        original = target.read_text(encoding="utf-8")
        payload["inspect_observed"] = True
        payload["original_sha256"] = sha256_text(original)

        content_block = f"### {args.target}\n{original}"
        prompt = repair_prompt_combine_topn.format(
            repair_relevant_file_instruction=repair_relevant_file_instruction,
            problem_statement=args.issue,
            content=content_block.rstrip(),
        ).strip()
        payload["prompt_sha256"] = sha256_text(prompt)
        payload["prompt_length"] = len(prompt)

        model = make_model(
            model=args.model,
            backend="openai",
            logger=logger,
            max_tokens=512,
            temperature=0,
            batch_size=1,
        )
        trajectory = model.codegen(prompt, num_samples=1)[0]
        payload["model_call_observed"] = True
        payload["termination_observed"] = True
        payload["raw_response"] = trajectory.get("response")
        payload["usage"] = trajectory.get("usage")

        raw_response = trajectory.get("response") or ""
        edited_file, new_content = _post_process_multifile_repair(
            raw_response,
            {args.target: original},
            logger,
            {args.target: [(1, max(1, len(original.splitlines())))]},
            diff_format=False,
        )
        payload["edit_parser_observed"] = True
        payload["edited_file"] = edited_file
        payload["parsed_content_sha256"] = sha256_text(new_content) if new_content else None

        if edited_file == args.target and new_content and new_content != original:
            target.write_text(new_content + ("\n" if not new_content.endswith("\n") else ""), encoding="utf-8", newline="\n")
            payload["edit_applied"] = True
            payload["final_sha256"] = sha256_text(target.read_text(encoding="utf-8"))

    except Exception as exc:
        payload["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
