import unittest

from arkx.characterization import RecommendedPath
from arkx.composition import Mechanism
from arkx.executor_qualification import ExecutorIdentity, QualificationStatus
from arkx.selection import (
    ExecutorBinding,
    ExecutorRegistry,
    SelectionReason,
    SelectionStatus,
    TreatmentCatalog,
    TreatmentDefinition,
    select_executor,
    select_treatment,
)


def binding(name="mini", status=QualificationStatus.QUALIFIABLE, evidence=("evidence://trial",), capabilities=("edit",)):
    return ExecutorBinding(
        ExecutorIdentity(name, "1.0", "adapter", f"digest-{name}"),
        capabilities,
        status,
        evidence,
    )


class SelectionTests(unittest.TestCase):
    def test_treatment_is_selected_after_path(self):
        treatment = TreatmentDefinition("simple-mini", RecommendedPath.SIMPLE_PATH, ("edit",), (Mechanism.P8_SAFE_EDITOR,))
        result = select_treatment(RecommendedPath.SIMPLE_PATH, TreatmentCatalog((treatment,)))
        self.assertEqual(result.status, SelectionStatus.SELECTED)
        self.assertEqual(result.treatment.name, "simple-mini")

    def test_ambiguous_treatments_require_qualification(self):
        catalog = TreatmentCatalog((TreatmentDefinition("a", RecommendedPath.SIMPLE_PATH), TreatmentDefinition("b", RecommendedPath.SIMPLE_PATH)))
        result = select_treatment(RecommendedPath.SIMPLE_PATH, catalog)
        self.assertEqual(result.status, SelectionStatus.REQUIRE_QUALIFICATION)
        self.assertIn(SelectionReason.AMBIGUOUS_TREATMENT, result.reason_codes)

    def test_missing_treatment_blocks(self):
        result = select_treatment(RecommendedPath.LOCALIZED_PATH, TreatmentCatalog(()))
        self.assertEqual(result.status, SelectionStatus.BLOCKED)

    def test_executor_requires_capability_and_evidence(self):
        treatment = TreatmentDefinition("localized", RecommendedPath.LOCALIZED_PATH, ("safe_edit",))
        result = select_executor(treatment, ExecutorRegistry((binding(capabilities=("edit",)),)))
        self.assertEqual(result.status, SelectionStatus.BLOCKED)
        self.assertIn(SelectionReason.NO_EXECUTOR_FOR_CAPABILITY, result.reason_codes)

    def test_unqualified_executor_cannot_be_selected(self):
        treatment = TreatmentDefinition("simple", RecommendedPath.SIMPLE_PATH, ("edit",))
        result = select_executor(treatment, ExecutorRegistry((binding(status=QualificationStatus.UNKNOWN, evidence=None),)))
        self.assertEqual(result.status, SelectionStatus.REQUIRE_QUALIFICATION)
        self.assertIn(SelectionReason.QUALIFICATION_EVIDENCE_MISSING, result.reason_codes)

    def test_multiple_qualified_executors_do_not_trigger_implicit_choice(self):
        treatment = TreatmentDefinition("simple", RecommendedPath.SIMPLE_PATH, ("edit",))
        result = select_executor(treatment, ExecutorRegistry((binding("a"), binding("b"))))
        self.assertEqual(result.status, SelectionStatus.REQUIRE_QUALIFICATION)
        self.assertIn(SelectionReason.AMBIGUOUS_EXECUTOR, result.reason_codes)

    def test_exactly_one_qualified_executor_is_selected(self):
        treatment = TreatmentDefinition("simple", RecommendedPath.SIMPLE_PATH, ("edit",))
        result = select_executor(treatment, ExecutorRegistry((binding(),)))
        self.assertEqual(result.status, SelectionStatus.SELECTED)
        self.assertEqual(result.executor.executor.name, "mini")

    def test_serialization_is_deterministic(self):
        treatment = TreatmentDefinition("simple", RecommendedPath.SIMPLE_PATH, ("edit",))
        registry = ExecutorRegistry((binding(),))
        self.assertEqual(select_executor(treatment, registry).to_json(), select_executor(treatment, registry).to_json())


if __name__ == "__main__":
    unittest.main()
