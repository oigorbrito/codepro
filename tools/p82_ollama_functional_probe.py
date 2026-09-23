"""Bounded functional T1 probe for locally served coding models."""

from __future__ import annotations

import argparse
import ast
import json
import time
from typing import Any

try:
    from tools.p82_ollama_probe import probe_model
except ModuleNotFoundError:  # direct `python tools/p82_ollama_functional_probe.py`
    from p82_ollama_probe import probe_model


FUNCTIONAL_PROMPT = (
    "Return only one valid JSON object with keys code and test. "
    "code must define validate_value(value): raise ValueError('value is required') "
    "when value is None, otherwise return value. test must use pytest.raises "
    "to check the None case and assert that validate_value(7) == 7."
)


def validate_functional_response(response: str) -> dict[str, Any]:
    payload = json.loads(response)
    if set(payload) != {"code", "test"}:
        raise ValueError("response keys must be exactly code and test")
    code = str(payload["code"])
    test = str(payload["test"])
    ast.parse(code)
    ast.parse(test)
    namespace: dict[str, Any] = {}
    exec(compile(code, "<model-code>", "exec"), namespace)  # noqa: S102 - bounded local probe
    function = namespace.get("validate_value")
    if not callable(function):
        raise ValueError("code did not define validate_value")
    try:
        function(None)
    except ValueError as error:
        if str(error) != "value is required":
            raise ValueError("wrong exception message") from error
    else:
        raise ValueError("None case did not raise ValueError")
    if function(7) != 7:
        raise ValueError("non-None case did not preserve value")
    if "pytest.raises" not in test:
        raise ValueError("test did not use pytest.raises")
    return {"code": code, "test": test}


def run_functional_probe(model: str, *, timeout_seconds: float = 35.0, num_predict: int = 128) -> dict[str, Any]:
    started = time.monotonic()
    result = probe_model(
        model,
        timeout_seconds=timeout_seconds,
        prompt=FUNCTIONAL_PROMPT,
        num_predict=num_predict,
        response_validator=validate_functional_response,
    )
    result["prompt_contract"] = FUNCTIONAL_PROMPT
    result["functional_status"] = result["status"]
    result["elapsed_seconds_total"] = round(time.monotonic() - started, 3)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model")
    parser.add_argument("--timeout", type=float, default=35.0)
    parser.add_argument("--num-predict", type=int, default=128)
    args = parser.parse_args()
    print(json.dumps(run_functional_probe(args.model, timeout_seconds=args.timeout, num_predict=args.num_predict), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
