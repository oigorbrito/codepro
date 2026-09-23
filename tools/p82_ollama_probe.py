"""Bounded, machine-readable Ollama T0 probe for P8.2 candidate qualification."""

from __future__ import annotations

import argparse
import json
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def probe_model(
    model: str,
    *,
    base_url: str = "http://127.0.0.1:11434",
    timeout_seconds: float = 35.0,
    prompt: str = "Respond with exactly ARKX_T0_OK and nothing else.",
    num_predict: int = 32,
    response_validator: Callable[[str], dict[str, Any]] | None = None,
    requester: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0, "num_predict": num_predict},
    }
    request = Request(
        f"{base_url.rstrip('/')}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    result: dict[str, Any] = {
        "model": model,
        "status": "INDETERMINATE",
        "timeout_seconds": timeout_seconds,
        "prompt_contract": payload["prompt"],
    }
    try:
        with requester(request, timeout=timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
        text = str(body.get("response", "")).strip()
        status = "PASS_T0_FORMAT" if body.get("done") and text == "ARKX_T0_OK" else "FORMAT_OR_CONTENT_FAIL"
        result.update({"status": status, "response": text, "done": body.get("done"), "eval_count": body.get("eval_count"), "total_duration": body.get("total_duration")})
        if response_validator is not None:
            try:
                result["validated"] = response_validator(text)
                result["status"] = "PASS_FUNCTIONAL" if body.get("done") else "FORMAT_OR_CONTENT_FAIL"
            except Exception as error:  # noqa: BLE001 - preserve validation boundary
                result.update({"status": "FORMAT_OR_CONTENT_FAIL", "validation_error": str(error)})
    except HTTPError as error:
        result.update({"status": "RUNTIME_FAILURE", "error_type": "HTTPError", "error": str(error)})
    except URLError as error:
        result.update({"status": "RUNTIME_FAILURE", "error_type": "URLError", "error": str(error)})
    except TimeoutError as error:
        result.update({"status": "TIMEOUT", "error_type": "TimeoutError", "error": str(error)})
    except Exception as error:  # noqa: BLE001 - probe must preserve concrete failure
        result.update({"status": "RUNTIME_FAILURE", "error_type": type(error).__name__, "error": str(error)})
    result["elapsed_seconds"] = round(time.monotonic() - started, 3)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("model")
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--timeout", type=float, default=35.0)
    args = parser.parse_args()
    print(json.dumps(probe_model(args.model, base_url=args.base_url, timeout_seconds=args.timeout), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
