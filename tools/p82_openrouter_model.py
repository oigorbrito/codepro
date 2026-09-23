"""Arkx OpenRouter adapter hardening for provider error envelopes."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
import time
from typing import Any

from arkx.integration import provider_error_envelope

try:
    from minisweagent.models.openrouter_model import OpenRouterModel as _OpenRouterModel
    MINISWEAGENT_AVAILABLE = True
except ModuleNotFoundError:  # dependency boundary; execution remains unavailable
    _OpenRouterModel = object
    MINISWEAGENT_AVAILABLE = False


class ProviderAvailabilityError(RuntimeError):
    """A provider returned a retryable availability error envelope."""

    def __init__(self, error: dict[str, Any]):
        self.error = error
        code = error.get("code")
        message = error.get("message", "")
        metadata = error.get("metadata", {})
        self.code = code
        self.provider_error_type = metadata.get("error_type") if isinstance(metadata, dict) else None
        super().__init__(
            f"provider_error code={code} error_type={self.provider_error_type}: {message}"
        )

    def to_error_envelope(self, *, raw_evidence_refs: tuple[str, ...] = ()):
        return provider_error_envelope({"error": self.error}, raw_evidence_refs=raw_evidence_refs)


class ArkxOpenRouterModel(_OpenRouterModel):
    """Keep provider error envelopes out of the success/action parser."""

    def __init__(self, *args, **kwargs):
        if not MINISWEAGENT_AVAILABLE:
            raise RuntimeError("minisweagent is required for ArkxOpenRouterModel execution")
        super().__init__(*args, **kwargs)

    def _diagnostics_path(self) -> Path | None:
        value = os.getenv("ARKX_P82_MODEL_DIAGNOSTICS_PATH")
        return Path(value) if value else None

    def _record_diagnostic(self, event: dict[str, Any]) -> None:
        path = self._diagnostics_path()
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"events": []}
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                payload = {"events": []}
        payload.setdefault("events", []).append(event)
        payload["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(path)

    def _query(self, messages: list[dict[str, str]], **kwargs):
        started = time.monotonic()
        event = {
            "event": "model_call",
            "started_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "model": self.config.model_name,
            "call_index": None,
            "timeout_origin": "provider_request",
        }
        path = self._diagnostics_path()
        if path and path.exists():
            try:
                prior = json.loads(path.read_text(encoding="utf-8"))
                event["call_index"] = len(prior.get("events", [])) + 1
            except (OSError, json.JSONDecodeError):
                event["call_index"] = 1
        try:
            response = super()._query(messages, **kwargs)
        except Exception as error:
            event.update({
                "finished_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                "duration_seconds": round(time.monotonic() - started, 3),
                "outcome": "exception",
                "exception_type": type(error).__name__,
                "exception": str(error),
            })
            self._record_diagnostic(event)
            raise
        event.update({
            "finished_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "duration_seconds": round(time.monotonic() - started, 3),
            "outcome": "provider_error_envelope" if isinstance(response, dict) and "error" in response else "response",
        })
        if isinstance(response, dict) and isinstance(response.get("error"), dict):
            error = response["error"]
            event.update({
                "provider_code": error.get("code"),
                "provider_error_type": (error.get("metadata") or {}).get("error_type") if isinstance(error.get("metadata"), dict) else None,
                "provider_message": error.get("message", ""),
                "timeout_origin": "provider_envelope",
            })
        self._record_diagnostic(event)
        return response

    def _parse_actions(self, response: dict) -> list[dict]:
        if isinstance(response, dict) and isinstance(response.get("error"), dict):
            self._record_diagnostic({
                "event": "adapter_classification",
                "at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                "outcome": "provider_availability_failure",
                "provider_code": response["error"].get("code"),
                "provider_error_type": (response["error"].get("metadata") or {}).get("error_type") if isinstance(response["error"].get("metadata"), dict) else None,
            })
            raise ProviderAvailabilityError(response["error"])
        if not MINISWEAGENT_AVAILABLE:
            raise KeyError("choices")
        return super()._parse_actions(response)
