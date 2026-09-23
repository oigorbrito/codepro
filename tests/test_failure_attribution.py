import json
import unittest
from dataclasses import replace
from pathlib import Path

from arkx.failure_attribution import (
    AttributionDomain,
    IssueDisposition,
    RunIssueAttribution,
    freeze_run_issue_attribution,
    validate_run_issue_attribution,
)


def valid(**overrides):
    values = {
        "attribution_id": "attr-001",
        "run_id": "run-001",
        "disposition": IssueDisposition.EXTERNAL_BLOCKER,
        "domain": AttributionDomain.PROVIDER,
        "observed_signature": "HTTP 503 provider_overloaded",
        "attribution_basis": "provider response explicitly reported temporary capacity exhaustion before patch execution",
        "evidence_refs": ("raw://provider-response.json",),
        "retryability": "bounded retry permitted by frozen run policy",
        "affects_primary_analysis": True,
    }
    values.update(overrides)
    return RunIssueAttribution(**values)


class ValidationTests(unittest.TestCase):
    def test_provider_availability_is_external_blocker(self):
        self.assertEqual(validate_run_issue_attribution(valid()), ())

    def test_unknown_cannot_be_promoted_to_failure(self):
        issues = validate_run_issue_attribution(
            valid(disposition=IssueDisposition.SYSTEM_FAILURE, domain=AttributionDomain.UNKNOWN)
        )
        self.assertIn(
            "UNKNOWN domain must remain UNKNOWN disposition until evidence supports attribution",
            issues,
        )

    def test_system_failure_requires_system_domain(self):
        issues = validate_run_issue_attribution(
            valid(disposition=IssueDisposition.SYSTEM_FAILURE, domain=AttributionDomain.PROVIDER)
        )
        self.assertIn("SYSTEM_FAILURE may only be attributed to SYSTEM_UNDER_TEST", issues)

    def test_external_blocker_cannot_blame_system(self):
        issues = validate_run_issue_attribution(
            valid(domain=AttributionDomain.SYSTEM_UNDER_TEST)
        )
        self.assertIn("EXTERNAL_BLOCKER must name a non-system external domain", issues)

    def test_attribution_requires_evidence(self):
        self.assertIn(
            "attribution requires at least one evidence reference",
            validate_run_issue_attribution(valid(evidence_refs=())),
        )


class FreezeTests(unittest.TestCase):
    def test_same_attribution_has_same_hash(self):
        self.assertEqual(
            freeze_run_issue_attribution(valid()).to_json(),
            freeze_run_issue_attribution(valid()).to_json(),
        )

    def test_domain_change_changes_hash(self):
        first = freeze_run_issue_attribution(valid())
        second = freeze_run_issue_attribution(
            replace(
                valid(),
                disposition=IssueDisposition.INVALID_RUN,
                domain=AttributionDomain.HARNESS,
            )
        )
        self.assertNotEqual(first.content_hash, second.content_hash)

    def test_invalid_attribution_cannot_be_frozen(self):
        with self.assertRaises(ValueError):
            freeze_run_issue_attribution(
                valid(disposition=IssueDisposition.SYSTEM_FAILURE, domain=AttributionDomain.PROVIDER)
            )


class FixtureTests(unittest.TestCase):
    def test_fixture_preserves_provider_blocker_semantics(self):
        path = Path(__file__).parents[1] / "experiments" / "failure-attribution-fixture.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        value = RunIssueAttribution.from_dict(payload["attribution"])
        self.assertEqual(payload["fixture_type"], "FAILURE_ATTRIBUTION_FIXTURE")
        self.assertEqual(value.disposition, IssueDisposition.EXTERNAL_BLOCKER)
        self.assertEqual(value.domain, AttributionDomain.PROVIDER)
        self.assertEqual(validate_run_issue_attribution(value), ())


if __name__ == "__main__":
    unittest.main()
