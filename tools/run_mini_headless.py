"""Headless mini-SWE-agent 2.x worker used by the Arkx adapter.

This file is intentionally tiny and uses the public Python API. It is not
called by unit tests and never evaluates acceptance.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> int:
    payload = json.load(sys.stdin)
    os.environ.setdefault("MSWEA_SILENT_STARTUP", "1")
    from minisweagent.agents import get_agent
    from minisweagent.config import get_config_from_spec
    from minisweagent.environments import get_environment
    from minisweagent.models import get_model
    from minisweagent.utils.serialize import recursive_merge, UNSET

    config = get_config_from_spec("mini.yaml")
    config = recursive_merge(config, {
        "run": {"task": payload["task"] or UNSET},
        "agent": {"mode": "yolo", "confirm_exit": False, "output_path": Path(payload["trajectory"])},
        "model": {"model_name": payload["model"], "model_class": payload.get("model_class", UNSET), **(payload.get("model_configuration") or payload.get("model_kwargs") or {})},
        "environment": {"cwd": payload["workspace"]},
    })
    model = get_model(config=config["model"])
    env = get_environment(config["environment"], default_type="local")
    agent = get_agent(model, env, config["agent"], default_type="default")
    result = agent.run(payload["task"] or "")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
