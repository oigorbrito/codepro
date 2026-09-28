import unittest

from arkx.configuration import ConfigurationSnapshot


class ConfigurationSnapshotTests(unittest.TestCase):
    def test_digest_is_stable_and_secret_material_is_not_serialized(self):
        first = ConfigurationSnapshot("executor", "1.0", {"temperature": 0, "mode": "strict"}, {"api_key": "sha256:key"})
        second = ConfigurationSnapshot("executor", "1.0", {"mode": "strict", "temperature": 0}, {"api_key": "sha256:key"})
        self.assertEqual(first.digest(), second.digest())
        self.assertNotIn("secret-value", first.to_json())
        self.assertEqual(first.reference, f"config://{first.digest()}")

    def test_configuration_identity_changes_with_public_or_secret_digest(self):
        base = ConfigurationSnapshot("executor", "1.0", {"mode": "strict"}, {"api_key": "a"})
        self.assertNotEqual(base.digest(), ConfigurationSnapshot("executor", "1.0", {"mode": "relaxed"}, {"api_key": "a"}).digest())
        self.assertNotEqual(base.digest(), ConfigurationSnapshot("executor", "1.0", {"mode": "strict"}, {"api_key": "b"}).digest())

    def test_empty_component_version_or_secret_digest_is_rejected(self):
        with self.assertRaises(ValueError):
            ConfigurationSnapshot("", "1.0", {})
        with self.assertRaises(ValueError):
            ConfigurationSnapshot("executor", "1.0", {}, {"api_key": ""})
