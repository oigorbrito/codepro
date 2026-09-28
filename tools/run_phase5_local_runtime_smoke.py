#!/usr/bin/env python3
"""Run the Phase 5 CodePro -> local llama.cpp HTTP smoke and persist evidence."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).parents[1].resolve()
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from arkx.local_runtime import (  # noqa: E402
    LocalRuntimeBinding,
    LocalRuntimeClient,
    LocalRuntimeError,
)


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--timeout-seconds", required=True, type=float)
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--expected", default="PHASE5_OK")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    evidence = Path(args.evidence_dir).resolve()
    if evidence.exists() and any(evidence.iterdir()):
        raise SystemExit(f"refusing to overwrite non-empty evidence directory: {evidence}")
    evidence.mkdir(parents=True, exist_ok=True)

    run_id = evidence.name
    captured_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    binding = LocalRuntimeBinding(args.base_url, args.model, args.timeout_seconds)
    snapshot = binding.configuration_snapshot()

    request_payload = {
        "model": binding.model_id,
        "messages": [{
            "role": "user",
            "content": f"Reply exactly {args.expected}",
        }],
        "max_tokens": 16,
        "temperature": 0,
        "stream": False,
    }

    write_json(evidence / "configuration.json", snapshot.to_dict())
    write_json(evidence / "request.json", request_payload)

    report: dict[str, Any] = {
        "schema_version": 1,
        "run_id": run_id,
        "captured_at": captured_at,
        "classification": "BLOCKED",
        "binding": {
            "base_url": binding.base_url,
            "model_id": binding.model_id,
            "timeout_seconds": binding.timeout_seconds,
            "configuration_digest": snapshot.digest(),
            "fallback": "DISABLED",
        },
        "expected_response": args.expected,
        "provider_api_cost_usd": 0,
        "failure": None,
        "response_valid": False,
        "telemetry": None,
    }

    try:
        result = LocalRuntimeClient(binding).chat_completion(
            request_payload["messages"],
            max_tokens=request_payload["max_tokens"],
            temperature=request_payload["temperature"],
        )
        write_json(evidence / "response.json", result.raw_response)
        report["response_valid"] = result.content.strip() == args.expected
        report["telemetry"] = {
            "wall_time_ms": result.wall_time_ms,
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            "total_tokens": result.total_tokens,
            "finish_reason": result.finish_reason,
            "model_id": result.model_id,
            "preflight": result.preflight.to_dict(),
        }
        report["classification"] = (
            "LOCAL_RUNTIME_PLUMBING_PASS"
            if report["response_valid"]
            else "MODEL_RESPONSE_INVALID"
        )
    except LocalRuntimeError as exc:
        report["failure"] = exc.to_dict()
        report["classification"] = f"{exc.kind.value}_FAILURE"

    write_json(evidence / "result.json", report)
    sys.stdout.write(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    return 0 if report["classification"] == "LOCAL_RUNTIME_PLUMBING_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
