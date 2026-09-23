"""Headless mini-SWE-agent 2.x worker used by the Arkx adapter.

This file is intentionally tiny and uses the public Python API. It is not
called by unit tests and never evaluates acceptance.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


def main() -> int:
    payload = json.load(sys.stdin)
    diagnostics_path = payload.get("diagnostics_path")
    if diagnostics_path:
        os.environ["ARKX_P82_MODEL_DIAGNOSTICS_PATH"] = diagnostics_path
    os.environ.setdefault("MSWEA_SILENT_STARTUP", "1")
    from minisweagent.agents import get_agent
    from minisweagent.config import get_config_from_spec
    from minisweagent.environments import get_environment
    from minisweagent.models import get_model
    from minisweagent.utils.serialize import recursive_merge, UNSET

    config = get_config_from_spec("mini.yaml")
    config = recursive_merge(
        config,
        {
            "run": {"task": payload["task"] or UNSET},
            "agent": {
                "mode": "yolo",
                "confirm_exit": False,
                "output_path": Path(payload["trajectory"]),
                "cost_limit": None if payload["max_cost"] is None else float(payload["max_cost"]),
                "wall_time_limit_seconds": None if payload["wall_time_seconds"] is None else int(payload["wall_time_seconds"]),
            },
            "model": {
                "model_name": payload["model"],
                "model_class": payload.get("model_class", UNSET),
                **(payload.get("model_configuration") or payload.get("model_kwargs") or {}),
            },
            "environment": {"cwd": payload["workspace"]},
        },
    )
    model = get_model(config=config["model"])
    if payload.get("environment") == "git-bash":
        from p82_bash_environment import BashLocalEnvironment

        environment_config = config["environment"] | {
            "bash_executable": payload["bash_executable"],
        }
        env = BashLocalEnvironment(**environment_config)
    else:
        env = get_environment(config["environment"], default_type="local")
    retry_limit = int(payload.get("provider_retry_attempts", 0))
    retry_backoff = float(payload.get("provider_retry_backoff_seconds", 0))
    result = None
    agent = None
    for retry_index in range(retry_limit + 1):
        try:
            agent = get_agent(model, env, config["agent"], default_type="default")
            result = agent.run(payload["task"] or "")
            break
        except Exception as error:
            from p82_openrouter_model import ProviderAvailabilityError

            if not isinstance(error, ProviderAvailabilityError):
                raise
            if retry_index >= retry_limit:
                result = {
                    "exit_status": "ProviderAvailabilityFailure",
                    "submission": "",
                    "failure_category": "PROVIDER_AVAILABILITY_FAILURE",
                    "provider_error": error.error,
                    "provider_retry_attempts": retry_index,
                }
                break
            if retry_backoff > 0:
                if diagnostics_path:
                    retry_path = Path(diagnostics_path).with_name("retry-observability.json")
                    retry_payload = {"events": []}
                    if retry_path.exists():
                        try:
                            retry_payload = json.loads(retry_path.read_text(encoding="utf-8"))
                        except (OSError, json.JSONDecodeError):
                            retry_payload = {"events": []}
                    retry_payload.setdefault("events", []).append({
                        "event": "provider_retry_backoff",
                        "retry_index": retry_index + 1,
                        "started_at": time.time(),
                        "backoff_seconds": retry_backoff,
                    })
                    temporary = retry_path.with_suffix(retry_path.suffix + ".tmp")
                    temporary.write_text(json.dumps(retry_payload, sort_keys=True) + "\n", encoding="utf-8")
                    temporary.replace(retry_path)
                time.sleep(retry_backoff)
            model = get_model(config=config["model"])
            env = get_environment(config["environment"], default_type="local") if payload.get("environment") != "git-bash" else BashLocalEnvironment(**environment_config)
    output = {
        "result": result,
        "usage": {
            "model_calls": getattr(agent, "n_calls", None),
            "cost": getattr(agent, "cost", None),
        },
    }
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
