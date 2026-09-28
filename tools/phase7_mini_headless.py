#!/usr/bin/env python3
"""Headless native mini-SWE-agent runner for Phase 7 compatibility."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from minisweagent.agents import get_agent
from minisweagent.config import get_config_from_spec
from minisweagent.environments import get_environment
from minisweagent.models import get_model
from minisweagent.utils.serialize import recursive_merge


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)

    config = recursive_merge(
        get_config_from_spec("mini.yaml"),
        get_config_from_spec(args.config),
    )
    agent_config = dict(config.get("agent", {}))
    agent_config.pop("mode", None)
    agent_config.pop("confirm_exit", None)
    agent_config["output_path"] = Path(args.output)

    model = get_model(config=config.get("model", {}))
    environment = get_environment(
        config.get("environment", {}),
        default_type="local",
    )
    agent = get_agent(
        model,
        environment,
        agent_config,
        default_type="default",
    )

    try:
        result = agent.run(args.task)
        print(json.dumps({"result": result}, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
