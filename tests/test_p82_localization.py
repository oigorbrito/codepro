import json
import unittest

from arkx.p82_localization import (
    LocalizationEvidenceBudget,
    TREATMENT,
    canonicalize_repository_relative_path,
    record_localization_artifact,
)


class P82LocalizationTests(unittest.TestCase):
    def budget(self):
        return LocalizationEvidenceBudget(max_files=2, max_symbols=3, max_context_lines=20)

    def test_contract_records_bounded_non_authoritative_candidates(self):
        artifact = record_localization_artifact(
            task_id="sympy__sympy-14711",
            repository_revision="abc123",
            localization_method="deterministic-candidate-pass-v1",
            candidate_files=("src/z.py", "src/a.py", "src/a.py"),
            candidate_symbols=("src/z.py::Z", "src/a.py::A"),
            context_lines_used=10,
            evidence_budget=self.budget(),
        )
        self.assertEqual(artifact.treatment, TREATMENT)
        self.assertEqual(artifact.candidate_files, ("src/a.py", "src/z.py"))
        self.assertTrue(artifact.candidates_are_non_authoritative)
        self.assertEqual(artifact.to_dict()["evidence_budget"]["max_files"], 2)

    def test_serialization_is_deterministic_and_contains_explicit_boundary(self):
        artifact = record_localization_artifact(
            task_id="task-1",
            repository_revision="deadbeef",
            localization_method="method-v1",
            candidate_files=("b.py", "a.py"),
            evidence_budget=self.budget(),
        )
        payload = json.loads(artifact.to_json())
        self.assertEqual(artifact.to_json(), artifact.to_json())
        self.assertEqual(payload["treatment"], "C1")
        self.assertTrue(payload["candidates_are_non_authoritative"])
        self.assertEqual(payload["candidate_files"], ["a.py", "b.py"])

    def test_budget_overflow_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "file count"):
            record_localization_artifact(
                task_id="task-1",
                repository_revision="rev",
                localization_method="method-v1",
                candidate_files=("a.py", "b.py", "c.py"),
                evidence_budget=self.budget(),
            )

    def test_symbol_and_context_overflow_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "symbol count"):
            record_localization_artifact(
                task_id="task-1",
                repository_revision="rev",
                localization_method="method-v1",
                candidate_symbols=("A", "B", "C", "D"),
                evidence_budget=self.budget(),
            )
        with self.assertRaisesRegex(ValueError, "context line count"):
            record_localization_artifact(
                task_id="task-1",
                repository_revision="rev",
                localization_method="method-v1",
                context_lines_used=21,
                evidence_budget=self.budget(),
            )

    def test_authoritative_candidates_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-authoritative"):
            from arkx.p82_localization import LocalizationArtifact

            LocalizationArtifact(
                task_id="task-1",
                repository_revision="rev",
                localization_method="method-v1",
                candidate_files=(),
                candidate_symbols=(),
                context_lines_used=0,
                evidence_budget=self.budget(),
                candidates_are_non_authoritative=False,
            )

    def test_absolute_and_traversal_paths_are_rejected(self):
        for path in (
            "C:/workspace/src/a.py",
            "C:\\workspace\\src\\a.py",
            "/workspace/src/a.py",
            "../src/a.py",
            "src/../a.py",
            "\\\\server\\share\\a.py",
            "C:foo",
            "",
            ".",
            "./",
        ):
            with self.subTest(path=path), self.assertRaises(ValueError):
                canonicalize_repository_relative_path(path)

    def test_paths_are_canonicalized_before_deduplication(self):
        artifact = record_localization_artifact(
            task_id="task-1",
            repository_revision="rev",
            localization_method="method-v2",
            candidate_files=("pkg\\sub\\module.py", "pkg/sub/module.py", "src/./a.py", "src/a.py"),
            evidence_budget=self.budget(),
        )
        self.assertEqual(artifact.candidate_files, ("pkg/sub/module.py", "src/a.py"))

    def test_canonicalization_is_deterministic_across_input_order(self):
        left = record_localization_artifact(
            task_id="task-1",
            repository_revision="rev",
            localization_method="method-v2",
            candidate_files=("src/./a.py", "pkg\\sub\\module.py"),
            evidence_budget=self.budget(),
        )
        right = record_localization_artifact(
            task_id="task-1",
            repository_revision="rev",
            localization_method="method-v2",
            candidate_files=("pkg/sub/module.py", "src/a.py"),
            evidence_budget=self.budget(),
        )
        self.assertEqual(left.to_json(), right.to_json())

    def test_zero_budget_is_a_valid_empty_contract(self):
        artifact = record_localization_artifact(
            task_id="task-1",
            repository_revision="rev",
            localization_method="method-v1",
            evidence_budget=LocalizationEvidenceBudget(0, 0, 0),
        )
        self.assertEqual(artifact.candidate_files, ())
        self.assertEqual(artifact.context_lines_used, 0)

    def test_trailing_separators_are_rejected_before_empty_segments_are_removed(self):
        for value in ("src/a.py/", "src/dir/", "src/a.py\\", "src/dir\\"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "trailing separator"):
                    canonicalize_repository_relative_path(value)

    def test_non_drive_colon_is_preserved(self):
        self.assertEqual(canonicalize_repository_relative_path("foo:bar"), "foo:bar")

    def test_drive_colons_remain_rejected(self):
        for value in ("C:foo", "C:/foo", "C:\\foo"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    canonicalize_repository_relative_path(value)


if __name__ == "__main__":
    unittest.main()
