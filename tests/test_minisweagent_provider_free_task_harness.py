import importlib.util
from pathlib import Path
import unittest


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


if __name__ == "__main__":
    unittest.main()
