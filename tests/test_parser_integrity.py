import json
import unittest
from pathlib import Path

from arkx.analysis_plan import AnalysisPlan
from arkx.measurement import MeasurementContract
from arkx.promotion import PromotionGate
from arkx.study import StudySpec
from arkx.treatment import TreatmentConfiguration
from arkx.workload import WorkloadManifest


ROOT = Path(__file__).parents[1]
EXPERIMENTS = ROOT / "experiments"


def fixture(name: str, key: str) -> dict:
    payload = json.loads((EXPERIMENTS / name).read_text(encoding="utf-8"))
    return dict(payload[key])


class ScientificContractParserTests(unittest.TestCase):
    def test_schema_version_is_never_string_coerced(self):
        cases = (
            (StudySpec, fixture("study-spec-fixture.json", "study_spec")),
            (WorkloadManifest, fixture("workload-manifest-fixture.json", "workload")),
            (TreatmentConfiguration, fixture("treatment-configuration-fixture.json", "configuration")),
            (AnalysisPlan, fixture("analysis-plan-fixture.json", "analysis_plan")),
            (MeasurementContract, fixture("measurement-contract-fixture.json", "contract")),
            (PromotionGate, fixture("promotion-gate-fixture.json", "gate")),
        )
        for cls, payload in cases:
            with self.subTest(contract=cls.__name__):
                payload = dict(payload)
                payload["schema_version"] = str(payload["schema_version"])
                with self.assertRaises(ValueError):
                    cls.from_dict(payload)

    def test_collection_fields_reject_strings(self):
        cases = (
            (StudySpec, fixture("study-spec-fixture.json", "study_spec"), "workload_refs"),
            (WorkloadManifest, fixture("workload-manifest-fixture.json", "workload"), "task_refs"),
            (TreatmentConfiguration, fixture("treatment-configuration-fixture.json", "configuration"), "fallback_targets"),
            (AnalysisPlan, fixture("analysis-plan-fixture.json", "analysis_plan"), "secondary_metrics"),
            (MeasurementContract, fixture("measurement-contract-fixture.json", "contract"), "metrics"),
            (PromotionGate, fixture("promotion-gate-fixture.json", "gate"), "criteria"),
            (PromotionGate, fixture("promotion-gate-fixture.json", "gate"), "required_evidence_keys"),
        )
        for cls, payload, field in cases:
            with self.subTest(contract=cls.__name__, field=field):
                payload = dict(payload)
                payload[field] = "not-a-collection"
                with self.assertRaises(ValueError):
                    cls.from_dict(payload)

    def test_integer_fields_reject_strings_and_booleans(self):
        cases = (
            (StudySpec, fixture("study-spec-fixture.json", "study_spec"), "repetitions"),
            (TreatmentConfiguration, fixture("treatment-configuration-fixture.json", "configuration"), "max_attempts"),
            (TreatmentConfiguration, fixture("treatment-configuration-fixture.json", "configuration"), "timeout_seconds"),
        )
        workload = fixture("workload-manifest-fixture.json", "workload")
        workload["random_seed"] = 7
        cases += ((WorkloadManifest, workload, "random_seed"),)

        for cls, payload, field in cases:
            for invalid in ("1", True):
                with self.subTest(contract=cls.__name__, field=field, invalid=invalid):
                    corrupted = dict(payload)
                    corrupted[field] = invalid
                    with self.assertRaises(ValueError):
                        cls.from_dict(corrupted)

    def test_analysis_confidence_level_rejects_string_and_boolean(self):
        payload = fixture("analysis-plan-fixture.json", "analysis_plan")
        for invalid in ("0.95", True):
            corrupted = dict(payload)
            corrupted["confidence_level"] = invalid
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    AnalysisPlan.from_dict(corrupted)


if __name__ == "__main__":
    unittest.main()
