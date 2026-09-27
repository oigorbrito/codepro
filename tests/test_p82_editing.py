import json
import unittest

from arkx.p82_editing import EditOperation, TREATMENT, record_edit_proposal


class P82EditingTests(unittest.TestCase):
    def test_replace_range_is_only_a_proposal(self):
        proposal = record_edit_proposal(
            task_id="task-1",
            target_file="src/example.py",
            operation=EditOperation.REPLACE_RANGE,
            replacement_content="return value",
            start_line=4,
            end_line=4,
        )
        self.assertEqual(proposal.treatment, TREATMENT)
        self.assertEqual(proposal.operation, EditOperation.REPLACE_RANGE)
        self.assertEqual(proposal.target_file, "src/example.py")
        self.assertEqual(proposal.to_dict()["replacement_content"], "return value")

    def test_patch_representation_is_supported_without_line_semantics(self):
        proposal = record_edit_proposal(
            task_id="task-1",
            target_file="src/example.py",
            operation="APPLY_PATCH",
            patch_content="@@ -1 +1 @@\n-old\n+new\n",
        )
        self.assertEqual(proposal.operation, EditOperation.APPLY_PATCH)
        self.assertIsNone(proposal.start_line)

    def test_serialization_is_deterministic(self):
        proposal = record_edit_proposal(
            task_id="task-1",
            target_file="src/example.py",
            operation=EditOperation.REPLACE_RANGE,
            replacement_content="new",
            start_line=1,
            end_line=2,
        )
        payload = json.loads(proposal.to_json())
        self.assertEqual(proposal.to_json(), proposal.to_json())
        self.assertEqual(payload["operation"], "REPLACE_RANGE")
        self.assertEqual(payload["treatment"], "B1")

    def test_unsupported_operations_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "unsupported"):
            record_edit_proposal(
                task_id="task-1",
                target_file="src/example.py",
                operation="DELETE_FILE",
                replacement_content="unused",
            )

    def test_mixed_representations_and_invalid_ranges_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "exactly one"):
            record_edit_proposal(
                task_id="task-1",
                target_file="src/example.py",
                operation=EditOperation.REPLACE_RANGE,
                replacement_content="new",
                patch_content="patch",
                start_line=1,
                end_line=1,
            )
        with self.assertRaisesRegex(ValueError, "line range"):
            record_edit_proposal(
                task_id="task-1",
                target_file="src/example.py",
                operation=EditOperation.REPLACE_RANGE,
                replacement_content="new",
                start_line=3,
                end_line=2,
            )


if __name__ == "__main__":
    unittest.main()
