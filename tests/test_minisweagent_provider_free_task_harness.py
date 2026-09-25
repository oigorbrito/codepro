import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).parents[1]
HARNESS_PATH = (
    ROOT
    / "experiments"
    / "integrations"
    / "minisweagent"
    / "provider_free_task_harness.py"
)


def load_harness():
    spec = importlib.util.spec_from_file_location("provider_free_task_harness", HARNESS_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ProviderFreeTaskHarnessTests(unittest.TestCase):
    def test_prepared_head_may_differ_when_base_is_ancestor_and_tree_is_clean(self):
        harness = load_harness()
        self.assertEqual(
            harness.classify_repo_state(ancestry_returncode=0, porcelain=""),
            "VALID_PREPARED_REPO_STATE",
        )

    def test_non_ancestor_is_material_mismatch(self):
        harness = load_harness()
        self.assertEqual(
            harness.classify_repo_state(ancestry_returncode=1, porcelain=""),
            "BASE_COMMIT_NOT_ANCESTOR",
        )

    def test_dirty_worktree_is_not_accepted(self):
        harness = load_harness()
        self.assertEqual(
            harness.classify_repo_state(
                ancestry_returncode=0,
                porcelain=" M sympy/core/basic.py\n",
            ),
            "WORKTREE_DIRTY",
        )

    def test_cleanup_falls_back_to_direct_docker_rm_when_upstream_cleanup_does_not_finish(self):
        harness = load_harness()

        class Env:
            container_id = "abc123"

            def cleanup(self):
                return None

        running = {
            "argv": ["docker", "inspect", "abc123"],
            "returncode": 0,
            "stdout": "[]",
            "stderr": "",
            "timeout": False,
            "error": None,
        }
        removed = {
            "argv": ["docker", "rm", "-f", "abc123"],
            "returncode": 0,
            "stdout": "abc123\n",
            "stderr": "",
            "timeout": False,
            "error": None,
        }
        absent = {
            "argv": ["docker", "inspect", "abc123"],
            "returncode": 1,
            "stdout": "",
            "stderr": "No such container",
            "timeout": False,
            "error": None,
        }

        with patch.object(harness, "_container_absent", side_effect=[(False, running), (True, absent)]), patch.object(
            harness, "_run", return_value=removed
        ):
            result = harness._cleanup_with_fallback(
                Env(),
                grace_seconds=0,
                poll_seconds=0,
            )

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["mode"], "CODEPRO_FORCED_DOCKER_RM")
        self.assertEqual(result["forced_cleanup"]["argv"], ["docker", "rm", "-f", "abc123"])

    def test_cleanup_reports_upstream_mode_when_container_is_already_absent(self):
        harness = load_harness()

        class Env:
            container_id = "abc123"

            def cleanup(self):
                return None

        absent = {
            "argv": ["docker", "inspect", "abc123"],
            "returncode": 1,
            "stdout": "",
            "stderr": "No such container",
            "timeout": False,
            "error": None,
        }

        with patch.object(harness, "_container_absent", return_value=(True, absent)):
            result = harness._cleanup_with_fallback(
                Env(),
                grace_seconds=1,
                poll_seconds=0,
            )

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["mode"], "UPSTREAM")


if __name__ == "__main__":
    unittest.main()
