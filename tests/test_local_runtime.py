import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from arkx.local_runtime import (
    LocalRuntimeBinding,
    LocalRuntimeClient,
    LocalRuntimeError,
    LocalRuntimeFailureKind,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self.payload


class LocalRuntimeBindingTests(unittest.TestCase):
    def test_binding_requires_loopback_v1_endpoint_and_explicit_timeout(self):
        binding = LocalRuntimeBinding(
            "http://127.0.0.1:8088/v1/",
            "phase5-granite",
            4.5,
        )
        self.assertEqual(binding.base_url, "http://127.0.0.1:8088/v1")
        self.assertEqual(binding.model_id, "phase5-granite")
        self.assertEqual(binding.timeout_seconds, 4.5)

        for bad in (
            "https://127.0.0.1:8088/v1",
            "http://example.com/v1",
            "http://127.0.0.1:8088",
            "http://127.0.0.1:8088/v1?x=1",
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    LocalRuntimeBinding(bad, "phase5-granite", 1)

        with self.assertRaises(ValueError):
            LocalRuntimeBinding("http://127.0.0.1:8088/v1", "phase5-granite", 0)

    def test_configuration_snapshot_records_binding_and_fallback_policy(self):
        binding = LocalRuntimeBinding("http://localhost:8088/v1", "phase5-granite", 5)
        snapshot = binding.configuration_snapshot()
        self.assertEqual(snapshot.component, "local-runtime-openai-http")
        self.assertEqual(snapshot.public_values["model_id"], "phase5-granite")
        self.assertEqual(snapshot.public_values["fallback"], "DISABLED")
        self.assertTrue(snapshot.reference.startswith("config://"))


class LocalRuntimeClientTests(unittest.TestCase):
    def binding(self):
        return LocalRuntimeBinding(
            "http://127.0.0.1:8088/v1",
            "phase5-granite",
            3,
        )

    @patch("arkx.local_runtime.urlopen")
    def test_success_uses_exact_model_and_timeout(self, opened):
        opened.side_effect = [
            FakeResponse({"status": "ok"}),
            FakeResponse({"data": [{"id": "phase5-granite", "object": "model"}]}),
            FakeResponse({
                "model": "phase5-granite",
                "choices": [{
                    "message": {"content": "PHASE5_OK"},
                    "finish_reason": "stop",
                }],
                "usage": {
                    "prompt_tokens": 4,
                    "completion_tokens": 2,
                    "total_tokens": 6,
                },
            }),
        ]

        response_format = {
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["PHASE5_OK"],
                    }
                },
                "required": ["status"],
                "additionalProperties": False,
            },
        }

        result = LocalRuntimeClient(self.binding()).chat_completion(
            [{"role": "user", "content": "Return the required JSON object."}],
            max_tokens=32,
            temperature=0,
            response_format=response_format,
        )

        self.assertEqual(result.content, "PHASE5_OK")
        self.assertEqual(result.model_id, "phase5-granite")
        self.assertEqual(result.total_tokens, 6)
        self.assertEqual(opened.call_count, 3)
        for call in opened.call_args_list:
            self.assertEqual(call.kwargs["timeout"], 3.0)

        request = opened.call_args_list[2].args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["model"], "phase5-granite")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["response_format"], response_format)

    @patch("arkx.local_runtime.urlopen")
    def test_model_mismatch_fails_without_chat_or_fallback(self, opened):
        opened.side_effect = [
            FakeResponse({"status": "ok"}),
            FakeResponse({"data": [{"id": "some-other-model"}]}),
        ]

        with self.assertRaises(LocalRuntimeError) as raised:
            LocalRuntimeClient(self.binding()).chat_completion(
                [{"role": "user", "content": "hello"}],
                max_tokens=4,
                temperature=0,
            )

        self.assertEqual(raised.exception.kind, LocalRuntimeFailureKind.MODEL)
        self.assertEqual(raised.exception.code, "MODEL_BINDING_MISMATCH")
        self.assertEqual(opened.call_count, 2)
        self.assertIn("fallback disabled", str(raised.exception))

    @patch("arkx.local_runtime.urlopen")
    def test_health_503_is_runtime_failure(self, opened):
        opened.side_effect = HTTPError(
            "http://127.0.0.1:8088/v1/health",
            503,
            "Loading model",
            {},
            io.BytesIO(b'{"error":{"message":"Loading model"}}'),
        )

        with self.assertRaises(LocalRuntimeError) as raised:
            LocalRuntimeClient(self.binding()).preflight()

        self.assertEqual(raised.exception.kind, LocalRuntimeFailureKind.RUNTIME)
        self.assertEqual(raised.exception.status_code, 503)

    @patch("arkx.local_runtime.urlopen")
    def test_transport_failure_is_http_failure(self, opened):
        opened.side_effect = URLError("connection refused")

        with self.assertRaises(LocalRuntimeError) as raised:
            LocalRuntimeClient(self.binding()).preflight()

        self.assertEqual(raised.exception.kind, LocalRuntimeFailureKind.HTTP)
        self.assertEqual(raised.exception.code, "HTTP_TRANSPORT_FAILURE")

    @patch("arkx.local_runtime.urlopen")
    def test_timeout_is_explicit_failure_kind(self, opened):
        opened.side_effect = TimeoutError("timed out")

        with self.assertRaises(LocalRuntimeError) as raised:
            LocalRuntimeClient(self.binding()).preflight()

        self.assertEqual(raised.exception.kind, LocalRuntimeFailureKind.TIMEOUT)
        self.assertEqual(raised.exception.code, "REQUEST_TIMEOUT")

    @patch("arkx.local_runtime.urlopen")
    def test_invalid_json_is_protocol_failure(self, opened):
        opened.return_value = FakeResponse(b"not-json")

        with self.assertRaises(LocalRuntimeError) as raised:
            LocalRuntimeClient(self.binding()).preflight()

        self.assertEqual(raised.exception.kind, LocalRuntimeFailureKind.PROTOCOL)

    @patch("arkx.local_runtime.urlopen")
    def test_response_model_mismatch_is_model_failure(self, opened):
        opened.side_effect = [
            FakeResponse({"status": "ok"}),
            FakeResponse({"data": [{"id": "phase5-granite"}]}),
            FakeResponse({
                "model": "wrong-model",
                "choices": [{
                    "message": {"content": "x"},
                    "finish_reason": "stop",
                }],
            }),
        ]

        with self.assertRaises(LocalRuntimeError) as raised:
            LocalRuntimeClient(self.binding()).chat_completion(
                [{"role": "user", "content": "hello"}],
                max_tokens=4,
                temperature=0,
            )

        self.assertEqual(raised.exception.kind, LocalRuntimeFailureKind.MODEL)
        self.assertEqual(raised.exception.code, "MODEL_RESPONSE_MISMATCH")


if __name__ == "__main__":
    unittest.main()
