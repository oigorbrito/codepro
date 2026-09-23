import json
import unittest

from tools.p82_ollama_functional_probe import validate_functional_response


class P82OllamaFunctionalProbeTests(unittest.TestCase):
    def test_valid_functional_response_is_accepted(self):
        response = json.dumps({
            "code": "def validate_value(value):\n    if value is None:\n        raise ValueError('value is required')\n    return value",
            "test": "with pytest.raises(ValueError, match='value is required'):\n    validate_value(None)\nassert validate_value(7) == 7",
        })
        result = validate_functional_response(response)
        self.assertIn("validate_value", result["code"])

    def test_wrong_exception_message_is_rejected(self):
        response = json.dumps({
            "code": "def validate_value(value):\n    if value is None:\n        raise ValueError('wrong')\n    return value",
            "test": "with pytest.raises(ValueError):\n    validate_value(None)",
        })
        with self.assertRaises(ValueError):
            validate_functional_response(response)

    def test_missing_pytest_assertion_is_rejected(self):
        response = json.dumps({
            "code": "def validate_value(value):\n    return value",
            "test": "assert validate_value(7) == 7",
        })
        with self.assertRaises(ValueError):
            validate_functional_response(response)

    def test_functional_budget_is_explicitly_overridable(self):
        from tools.p82_ollama_probe import probe_model

        captured = {}

        def requester(request, timeout):
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return type("Response", (), {"__enter__": lambda self: self, "__exit__": lambda *args: False, "read": lambda self: json.dumps({"response": "{}", "done": True}).encode("utf-8")})()

        probe_model("model", prompt="functional", num_predict=128, requester=requester)
        self.assertEqual(captured["body"]["options"]["num_predict"], 128)


if __name__ == "__main__":
    unittest.main()
