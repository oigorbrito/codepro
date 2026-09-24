import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).parents[1]
PREFLIGHT_PATH = ROOT / "experiments" / "integrations" / "minisweagent" / "preflight.py"
REFERENCE_PATH = (
    ROOT
    / "experiments"
    / "integrations"
    / "minisweagent"
    / "swebench-v2.4.6-reference.yaml"
)


def load_preflight():
    spec = importlib.util.spec_from_file_location("mini_preflight", PREFLIGHT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class MiniPreflightIdentityTests(unittest.TestCase):
    def test_config_identity_uses_committed_git_blob_not_worktree_eol(self):
        preflight = load_preflight()
        reference = REFERENCE_PATH.read_text(encoding="utf-8")

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=repo,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "CodePro Test"],
                cwd=repo,
                check=True,
            )

            config_path = repo / preflight.BUNDLED_CONFIG
            config_path.parent.mkdir(parents=True)
            config_path.write_text(reference, encoding="utf-8", newline="\n")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "reference"], cwd=repo, check=True, capture_output=True)

            committed_blob = subprocess.run(
                ["git", "rev-parse", f"HEAD:{preflight.BUNDLED_CONFIG.as_posix()}"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(committed_blob, preflight.PINNED_CONFIG_BLOB_SHA)

            # Simulate a Windows-materialized worktree. The committed Git object
            # remains LF-normalized even though filesystem bytes are CRLF.
            config_path.write_bytes(reference.replace("\n", "\r\n").encode("utf-8"))

            result = preflight._check_config(repo)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["git_blob_sha"], preflight.PINNED_CONFIG_BLOB_SHA)


if __name__ == "__main__":
    unittest.main()
