import hashlib
from pathlib import Path
import unittest


PINNED_CONFIG_BLOB_SHA = "106decd160e72e5164e29d15d23da354c29c309d"


def git_blob_sha(path: Path) -> str:
    payload = path.read_bytes()
    header = f"blob {len(payload)}\0".encode()
    return hashlib.sha1(header + payload).hexdigest()


class MiniSwebenchReferenceTests(unittest.TestCase):
    def setUp(self):
        self.path = (
            Path(__file__).parents[1]
            / "experiments"
            / "integrations"
            / "minisweagent"
            / "swebench-v2.4.6-reference.yaml"
        )
        self.text = self.path.read_text(encoding="utf-8")

    def test_reference_config_matches_pinned_upstream_blob(self):
        self.assertEqual(git_blob_sha(self.path), PINNED_CONFIG_BLOB_SHA)

    def test_reference_config_uses_benchmarked_docker_substrate(self):
        self.assertIn('cwd: "/testbed"', self.text)
        self.assertIn('interpreter: ["bash", "-c"]', self.text)
        self.assertIn("BASH_ENV: /root/.bashrc", self.text)
        self.assertIn("environment_class: docker", self.text)

    def test_reference_config_does_not_select_local_or_swerex_backend(self):
        self.assertNotIn("environment_class: local", self.text)
        self.assertNotIn("environment_class: swerex_docker", self.text)
        self.assertNotIn("environment_class: swerex_modal", self.text)


if __name__ == "__main__":
    unittest.main()
