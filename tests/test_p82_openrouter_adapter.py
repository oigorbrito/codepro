import unittest

from tools.p82_openrouter_model import ArkxOpenRouterModel, ProviderAvailabilityError


class P82OpenRouterAdapterTests(unittest.TestCase):
    def test_provider_error_envelope_is_not_parsed_as_success(self):
        model = ArkxOpenRouterModel.__new__(ArkxOpenRouterModel)
        with self.assertRaises(ProviderAvailabilityError) as raised:
            model._parse_actions({
                "error": {
                    "code": 503,
                    "message": "Upstream error from Nvidia: Service temporarily overloaded",
                    "metadata": {"error_type": "provider_overloaded"},
                }
            })
        self.assertIn("code=503", str(raised.exception))
        self.assertEqual(raised.exception.provider_error_type, "provider_overloaded")

    def test_missing_choices_without_error_remains_non_provider_failure(self):
        model = ArkxOpenRouterModel.__new__(ArkxOpenRouterModel)
        with self.assertRaises(KeyError):
            model._parse_actions({"unexpected": "payload"})

    def test_provider_error_can_cross_neutral_error_boundary(self):
        model = ArkxOpenRouterModel.__new__(ArkxOpenRouterModel)
        with self.assertRaises(ProviderAvailabilityError) as raised:
            model._parse_actions({"error": {"code": 429, "message": "rate limited"}})
        envelope = raised.exception.to_error_envelope(raw_evidence_refs=("artifact://provider.json",))
        self.assertEqual(envelope.domain.value, "PROVIDER")
        self.assertEqual(envelope.code, "PROVIDER_429")
        self.assertEqual(envelope.raw_evidence_refs, ("artifact://provider.json",))
