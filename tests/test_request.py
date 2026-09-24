import unittest

from arkx.characterization import Scope, TaskSignals
from arkx.request import (
    ArkxRequest,
    GovernancePolicy,
    GovernanceReason,
    GovernanceStatus,
    RequestBudget,
    RequestEnvironment,
    authorize_request,
    characterize_authorized_request,
)


def valid_request(**overrides):
    values = {
        "request_id": "req-1",
        "task_id": "task-1",
        "requester": "developer",
        "signals": TaskSignals(
            candidate_files=("src/arkx/example.py",),
            dependency_edges=(),
            affected_components=("example",),
            known_tests=("tests/test_example.py",),
            ambiguity_markers=(),
            risk_markers=(),
            acceptance_checks=("tests pass",),
        ),
        "authorized_paths": ("src/arkx",),
        "budget": RequestBudget(max_attempts=2, max_tokens=1000, max_wall_time_ms=10000),
        "environment": RequestEnvironment("local", "workspace", "HEAD"),
        "acceptance_authority": "authority-1",
    }
    values.update(overrides)
    return ArkxRequest(**values)


def policy(**overrides):
    values = {
        "authority_id": "governance-1",
        "allowed_requesters": ("developer",),
        "allowed_environments": ("local",),
        "max_attempts": 3,
        "max_tokens": 2000,
        "max_wall_time_ms": 20000,
    }
    values.update(overrides)
    return GovernancePolicy(**values)


class GovernanceTests(unittest.TestCase):
    def test_valid_request_is_authorized(self):
        result = authorize_request(valid_request(), policy())
        self.assertEqual(result.status, GovernanceStatus.AUTHORIZED)
        self.assertEqual(result.reason_codes, (GovernanceReason.AUTHORIZED,))

    def test_missing_authority_scope_or_budget_is_blocked(self):
        result = authorize_request(
            valid_request(authorized_paths=None, budget=None, acceptance_authority=None),
            policy(),
        )
        self.assertEqual(result.status, GovernanceStatus.BLOCKED)
        self.assertIn(GovernanceReason.AUTHORIZED_SCOPE_MISSING, result.reason_codes)
        self.assertIn(GovernanceReason.BUDGET_MISSING, result.reason_codes)
        self.assertIn(GovernanceReason.ACCEPTANCE_AUTHORITY_MISSING, result.reason_codes)
        self.assertIsNone(result.request)

    def test_out_of_scope_file_is_blocked(self):
        result = authorize_request(
            valid_request(
                signals=valid_request().signals.__class__(
                    candidate_files=("outside.py",),
                    dependency_edges=(),
                    affected_components=("example",),
                    known_tests=("tests/test_example.py",),
                    ambiguity_markers=(),
                    risk_markers=(),
                    acceptance_checks=("tests pass",),
                )
            ),
            policy(),
        )
        self.assertEqual(result.status, GovernanceStatus.BLOCKED)
        self.assertIn(GovernanceReason.PATH_OUTSIDE_AUTHORIZED_SCOPE, result.reason_codes)

    def test_budget_over_policy_is_blocked(self):
        result = authorize_request(valid_request(budget=RequestBudget(max_attempts=4)), policy(max_attempts=3))
        self.assertEqual(result.status, GovernanceStatus.BLOCKED)
        self.assertIn(GovernanceReason.BUDGET_EXCEEDED, result.reason_codes)

    def test_environment_and_requester_are_policy_bound(self):
        result = authorize_request(
            valid_request(requester="unknown", environment=RequestEnvironment("remote", "workspace", "HEAD")),
            policy(),
        )
        self.assertEqual(result.status, GovernanceStatus.BLOCKED)
        self.assertIn(GovernanceReason.REQUESTER_NOT_ALLOWED, result.reason_codes)
        self.assertIn(GovernanceReason.ENVIRONMENT_NOT_ALLOWED, result.reason_codes)

    def test_environment_requires_workspace_and_revision(self):
        result = authorize_request(
            valid_request(environment=RequestEnvironment("local", None, None)),
            policy(),
        )
        self.assertEqual(result.status, GovernanceStatus.BLOCKED)
        self.assertIn(GovernanceReason.WORKSPACE_MISSING, result.reason_codes)
        self.assertIn(GovernanceReason.REVISION_MISSING, result.reason_codes)

    def test_unauthorized_request_cannot_be_characterized(self):
        decision = authorize_request(valid_request(authorized_paths=None), policy())
        self.assertIsNone(characterize_authorized_request(decision))

    def test_authorized_request_is_characterized_without_selecting_executor(self):
        decision = authorize_request(valid_request(), policy())
        result = characterize_authorized_request(decision)
        self.assertEqual(result.scope, Scope.SIMPLE)
        self.assertNotIn("executor", result.to_dict())

    def test_serialization_is_deterministic(self):
        first = authorize_request(valid_request(), policy()).to_json()
        second = authorize_request(valid_request(), policy()).to_json()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
