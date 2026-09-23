import json
import unittest

from tools.p82_ollama_probe import probe_model


class FakeResponse:
    def __init__(self, body):
        self.body = json.dumps(body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


class P82OllamaProbeTests(unittest.TestCase):
    def test_exact_response_is_t0_pass(self):
        result = probe_model(
            "gemma3:4b",
            requester=lambda request, timeout: FakeResponse({"response": "ARKX_T0_OK", "done": True, "eval_count": 9}),
        )
        self.assertEqual(result["status"], "PASS_T0_FORMAT")
        self.assertEqual(result["eval_count"], 9)

    def test_non_exact_response_is_not_pass(self):
        result = probe_model(
            "model",
            requester=lambda request, timeout: FakeResponse({"response": "almost", "done": True}),
        )
        self.assertEqual(result["status"], "FORMAT_OR_CONTENT_FAIL")

    def test_timeout_is_explicit(self):
        def timeout(request, timeout):
            raise TimeoutError("bounded timeout")

        result = probe_model("model", requester=timeout, timeout_seconds=1)
        self.assertEqual(result["status"], "TIMEOUT")
        self.assertEqual(result["error_type"], "TimeoutError")


if __name__ == "__main__":
    unittest.main()
