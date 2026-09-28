"""Explicit local llama.cpp HTTP binding for CodePro.

This module is transport plumbing only. It does not select a model, choose an
executor, verify task output, accept a task, or promote a runtime/model.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import ipaddress
import json
import socket
import time
from typing import Any, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .configuration import ConfigurationSnapshot


class LocalRuntimeFailureKind(str, Enum):
    HTTP = "HTTP"
    RUNTIME = "RUNTIME"
    MODEL = "MODEL"
    TIMEOUT = "TIMEOUT"
    PROTOCOL = "PROTOCOL"


class LocalRuntimeError(RuntimeError):
    """Typed local-runtime failure that preserves the failing boundary."""

    def __init__(
        self,
        kind: LocalRuntimeFailureKind,
        code: str,
        message: str,
        *,
        status_code: int | None = None,
    ) -> None:
        if not code.strip() or not message.strip():
            raise ValueError("local runtime error code and message must be non-empty")
        super().__init__(message)
        self.kind = kind
        self.code = code
        self.status_code = status_code

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "code": self.code,
            "message": str(self),
            "status_code": self.status_code,
        }


@dataclass(frozen=True)
class LocalRuntimeBinding:
    """Exact loopback endpoint + model binding with an explicit timeout."""

    base_url: str
    model_id: str
    timeout_seconds: float

    def __post_init__(self) -> None:
        base_url = self.base_url.rstrip("/")
        model_id = self.model_id.strip()
        if not base_url or not model_id:
            raise ValueError("local runtime base_url and model_id must be non-empty")
        if isinstance(self.timeout_seconds, bool) or self.timeout_seconds <= 0:
            raise ValueError("local runtime timeout_seconds must be positive")

        parsed = urlsplit(base_url)
        if parsed.scheme != "http":
            raise ValueError("Phase 5 local runtime requires an explicit http loopback endpoint")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("credentials must not be embedded in the local runtime URL")
        if parsed.query or parsed.fragment:
            raise ValueError("local runtime base_url must not contain query or fragment")
        if parsed.path.rstrip("/") != "/v1":
            raise ValueError("local runtime base_url must end in /v1")
        host = parsed.hostname
        if host is None:
            raise ValueError("local runtime base_url requires a host")
        if host.lower() != "localhost":
            try:
                address = ipaddress.ip_address(host)
            except ValueError as exc:
                raise ValueError(
                    "Phase 5 local runtime endpoint must be localhost or a loopback IP"
                ) from exc
            if not address.is_loopback:
                raise ValueError("Phase 5 local runtime endpoint must be loopback-only")

        object.__setattr__(self, "base_url", base_url)
        object.__setattr__(self, "model_id", model_id)
        object.__setattr__(self, "timeout_seconds", float(self.timeout_seconds))

    def configuration_snapshot(self) -> ConfigurationSnapshot:
        return ConfigurationSnapshot(
            component="local-runtime-openai-http",
            version="1",
            public_values={
                "base_url": self.base_url,
                "model_id": self.model_id,
                "timeout_seconds": self.timeout_seconds,
                "fallback": "DISABLED",
            },
        )


@dataclass(frozen=True)
class LocalRuntimePreflight:
    model_id: str
    model_metadata: Mapping[str, Any]
    health: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "model_metadata": dict(self.model_metadata),
            "health": dict(self.health),
        }


@dataclass(frozen=True)
class LocalRuntimeChatResult:
    model_id: str
    content: str
    wall_time_ms: int
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    finish_reason: str | None
    preflight: LocalRuntimePreflight
    raw_response: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "content": self.content,
            "wall_time_ms": self.wall_time_ms,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "finish_reason": self.finish_reason,
            "preflight": self.preflight.to_dict(),
            "raw_response": dict(self.raw_response),
        }


class LocalRuntimeClient:
    """Fail-closed client for one exact llama.cpp server/model binding."""

    def __init__(self, binding: LocalRuntimeBinding) -> None:
        self.binding = binding

    def _url(self, suffix: str) -> str:
        if not suffix.startswith("/"):
            raise ValueError("local runtime path suffix must start with /")
        return self.binding.base_url + suffix

    def _request_json(
        self,
        method: str,
        suffix: str,
        *,
        payload: Mapping[str, Any] | None = None,
        http_error_kind: LocalRuntimeFailureKind = LocalRuntimeFailureKind.HTTP,
    ) -> Mapping[str, Any]:
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(
                payload, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = Request(self._url(suffix), data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.binding.timeout_seconds) as response:
                raw = response.read()
        except HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", errors="replace")
            except Exception:
                detail = ""
            message = f"local runtime HTTP {exc.code} at {suffix}"
            if detail.strip():
                message += f": {detail.strip()}"
            raise LocalRuntimeError(
                http_error_kind,
                f"{http_error_kind.value}_HTTP_{exc.code}",
                message,
                status_code=exc.code,
            ) from exc
        except (TimeoutError, socket.timeout) as exc:
            raise LocalRuntimeError(
                LocalRuntimeFailureKind.TIMEOUT,
                "REQUEST_TIMEOUT",
                f"local runtime request exceeded {self.binding.timeout_seconds:g}s at {suffix}",
            ) from exc
        except URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                raise LocalRuntimeError(
                    LocalRuntimeFailureKind.TIMEOUT,
                    "REQUEST_TIMEOUT",
                    f"local runtime request exceeded {self.binding.timeout_seconds:g}s at {suffix}",
                ) from exc
            raise LocalRuntimeError(
                LocalRuntimeFailureKind.HTTP,
                "HTTP_TRANSPORT_FAILURE",
                f"local runtime transport failure at {suffix}: {exc.reason}",
            ) from exc
        except OSError as exc:
            raise LocalRuntimeError(
                LocalRuntimeFailureKind.HTTP,
                "HTTP_TRANSPORT_FAILURE",
                f"local runtime transport failure at {suffix}: {exc}",
            ) from exc

        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LocalRuntimeError(
                LocalRuntimeFailureKind.PROTOCOL,
                "INVALID_JSON_RESPONSE",
                f"local runtime returned invalid JSON at {suffix}",
            ) from exc
        if not isinstance(decoded, Mapping):
            raise LocalRuntimeError(
                LocalRuntimeFailureKind.PROTOCOL,
                "INVALID_JSON_SHAPE",
                f"local runtime returned a non-object JSON payload at {suffix}",
            )
        return decoded

    def preflight(self) -> LocalRuntimePreflight:
        health = self._request_json(
            "GET",
            "/health",
            http_error_kind=LocalRuntimeFailureKind.RUNTIME,
        )
        if health.get("status") != "ok":
            raise LocalRuntimeError(
                LocalRuntimeFailureKind.RUNTIME,
                "RUNTIME_NOT_READY",
                "local runtime health endpoint did not report status=ok",
            )

        models = self._request_json("GET", "/models")
        data = models.get("data")
        if not isinstance(data, list):
            raise LocalRuntimeError(
                LocalRuntimeFailureKind.PROTOCOL,
                "INVALID_MODELS_RESPONSE",
                "local runtime models response is missing a data list",
            )

        exact: Mapping[str, Any] | None = None
        observed_ids: list[str] = []
        for item in data:
            if not isinstance(item, Mapping):
                continue
            candidate = item.get("id")
            if isinstance(candidate, str):
                observed_ids.append(candidate)
                if candidate == self.binding.model_id:
                    exact = item

        if exact is None:
            raise LocalRuntimeError(
                LocalRuntimeFailureKind.MODEL,
                "MODEL_BINDING_MISMATCH",
                "configured model was not exposed by the bound endpoint; "
                f"configured={self.binding.model_id!r}, observed={observed_ids!r}; "
                "fallback disabled",
            )

        return LocalRuntimePreflight(self.binding.model_id, exact, health)

    def chat_completion(
        self,
        messages: Sequence[Mapping[str, str]],
        *,
        max_tokens: int,
        temperature: float,
        response_format: Mapping[str, Any] | None = None,
    ) -> LocalRuntimeChatResult:
        if not messages:
            raise ValueError("messages must be non-empty")
        normalized_messages: list[dict[str, str]] = []
        for message in messages:
            role = message.get("role")
            content = message.get("content")
            if not isinstance(role, str) or not role.strip():
                raise ValueError("each message requires a non-empty role")
            if not isinstance(content, str) or not content.strip():
                raise ValueError("each message requires non-empty content")
            normalized_messages.append({"role": role, "content": content})
        if isinstance(max_tokens, bool) or max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if isinstance(temperature, bool) or temperature < 0:
            raise ValueError("temperature must be non-negative")
        if response_format is not None and not isinstance(response_format, Mapping):
            raise ValueError("response_format must be a mapping when provided")

        preflight = self.preflight()
        payload = {
            "model": self.binding.model_id,
            "messages": normalized_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False,
        }
        if response_format is not None:
            payload["response_format"] = dict(response_format)

        started = time.perf_counter()
        response = self._request_json("POST", "/chat/completions", payload=payload)
        wall_time_ms = round((time.perf_counter() - started) * 1000)

        response_model = response.get("model")
        if isinstance(response_model, str) and response_model != self.binding.model_id:
            raise LocalRuntimeError(
                LocalRuntimeFailureKind.MODEL,
                "MODEL_RESPONSE_MISMATCH",
                f"local runtime responded as {response_model!r}, "
                f"expected {self.binding.model_id!r}",
            )

        choices = response.get("choices")
        if (
            not isinstance(choices, list)
            or not choices
            or not isinstance(choices[0], Mapping)
        ):
            raise LocalRuntimeError(
                LocalRuntimeFailureKind.PROTOCOL,
                "INVALID_CHAT_RESPONSE",
                "local runtime chat response is missing choices[0]",
            )
        first = choices[0]
        message = first.get("message")
        if not isinstance(message, Mapping) or not isinstance(message.get("content"), str):
            raise LocalRuntimeError(
                LocalRuntimeFailureKind.PROTOCOL,
                "INVALID_CHAT_RESPONSE",
                "local runtime chat response is missing choices[0].message.content",
            )

        usage = response.get("usage")
        if not isinstance(usage, Mapping):
            usage = {}

        def optional_int(name: str) -> int | None:
            value = usage.get(name)
            if value is None:
                return None
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise LocalRuntimeError(
                    LocalRuntimeFailureKind.PROTOCOL,
                    "INVALID_USAGE_RESPONSE",
                    f"local runtime usage.{name} must be a non-negative integer",
                )
            return value

        finish_reason = first.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            raise LocalRuntimeError(
                LocalRuntimeFailureKind.PROTOCOL,
                "INVALID_CHAT_RESPONSE",
                "local runtime finish_reason must be a string when present",
            )

        return LocalRuntimeChatResult(
            model_id=self.binding.model_id,
            content=str(message["content"]),
            wall_time_ms=wall_time_ms,
            prompt_tokens=optional_int("prompt_tokens"),
            completion_tokens=optional_int("completion_tokens"),
            total_tokens=optional_int("total_tokens"),
            finish_reason=finish_reason,
            preflight=preflight,
            raw_response=response,
        )
