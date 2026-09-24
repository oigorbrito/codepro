import json
import unittest

from arkx.governance import (
    AuthorityGrant,
    GovernanceDecision,
    GovernanceReason,
    GovernanceStatus,
    TaskRequest,
    evaluate_governance,
)


def request(*, scope=("src/a.py",), permissions=("edit",)):
    return TaskRequest(
        request_id="request-1",
        requester_ref="user://fixture",
        task_ref="task://fixture",
        project_ref="git://repo@base",
        requested_scope=scope,
        required_permissions=permissions,
    )


def grant(**overrides):
    values = {
        "grant_id": "grant-1",
        "request_id": "request-1",
        "authority_ref": "authority://fixture",
        "authorized_scope": ("src/a.py", "tests/test_a.py"),
        "permissions": ("edit", "test"),
        "max_commands": 20,
        "max_wall_time_seconds": 300,
        "environment_ref": "environment://local-fixture",
        "acceptance_authority_ref": "acceptance://reviewer",
        "evidence_refs": ("evidence://authorization",),
    }
    values.update(overrides)
    return AuthorityGrant(**values)


class GovernanceDecisionTests(unittest.TestCase):
    def test_complete_authority_authorizes_request(self):
        result = evaluate_governance(request(), grant())
        self.assertEqual(result.status, GovernanceStatus.AUTHORIZED)
        self.assertEqual(result.reasons, (GovernanceReason.AUTHORIZED,))
        self.assertEqual(result.max_commands, 20)
        self.assertEqual(result.max_wall_time_seconds, 300.0)
        self.assertEqual(result.environment_ref, "environment://local-fixture")
        self.assertEqual(result.acceptance_authority_ref, "acceptance://reviewer")
        self.assertEqual(result.evidence_refs, ("evidence://authorization",))

    def test_missing_authority_is_blocked(self):
        result = evaluate_governance(request(), None)
        self.assertEqual(result.status, GovernanceStatus.BLOCKED)
        self.assertEqual(result.reasons, (GovernanceReason.MISSING_AUTHORITY,))
        self.assertIsNone(result.grant_id)

    def test_grant_for_another_request_is_blocked(self):
        result = evaluate_governance(
            request(),
            grant(request_id="other-request"),
        )
        self.assertEqual(result.status, GovernanceStatus.BLOCKED)
        self.assertEqual(
            result.reasons,
            (GovernanceReason.AUTHORITY_REQUEST_MISMATCH,),
        )

    def test_missing_scope_or_budget_remains_unknown_not_denied(self):
        scope_unknown = evaluate_governance(
            request(),
            grant(authorized_scope=None),
        )
        self.assertEqual(scope_unknown.status, GovernanceStatus.UNKNOWN)
        self.assertIn(GovernanceReason.SCOPE_UNKNOWN, scope_unknown.reasons)

        budget_unknown = evaluate_governance(
            request(),
            grant(max_commands=None, max_wall_time_seconds=None),
        )
        self.assertEqual(budget_unknown.status, GovernanceStatus.UNKNOWN)
        self.assertIn(GovernanceReason.BUDGET_UNKNOWN, budget_unknown.reasons)

    def test_all_incomplete_authority_fields_are_reported(self):
        result = evaluate_governance(
            request(),
            grant(
                authorized_scope=None,
                permissions=None,
                max_commands=None,
                max_wall_time_seconds=None,
                environment_ref=None,
                acceptance_authority_ref=None,
            ),
        )
        self.assertEqual(result.status, GovernanceStatus.UNKNOWN)
        self.assertEqual(
            set(result.reasons),
            {
                GovernanceReason.SCOPE_UNKNOWN,
                GovernanceReason.PERMISSIONS_UNKNOWN,
                GovernanceReason.BUDGET_UNKNOWN,
                GovernanceReason.ENVIRONMENT_UNKNOWN,
                GovernanceReason.ACCEPTANCE_AUTHORITY_UNKNOWN,
            },
        )

    def test_scope_outside_authority_is_blocked(self):
        result = evaluate_governance(
            request(scope=("src/a.py", "src/b.py")),
            grant(),
        )
        self.assertEqual(result.status, GovernanceStatus.BLOCKED)
        self.assertEqual(result.reasons, (GovernanceReason.SCOPE_DENIED,))

    def test_permission_outside_authority_is_blocked(self):
        result = evaluate_governance(
            request(permissions=("edit", "network")),
            grant(),
        )
        self.assertEqual(result.status, GovernanceStatus.BLOCKED)
        self.assertEqual(result.reasons, (GovernanceReason.PERMISSION_DENIED,))

    def test_scope_and_permission_order_do_not_change_decision(self):
        first = evaluate_governance(
            request(scope=("src/a.py",), permissions=("edit",)),
            grant(
                authorized_scope=("tests/test_a.py", "src/a.py"),
                permissions=("test", "edit"),
            ),
        )
        second = evaluate_governance(
            request(scope=("src/a.py",), permissions=("edit",)),
            grant(
                authorized_scope=("src/a.py", "tests/test_a.py"),
                permissions=("edit", "test"),
            ),
        )
        self.assertEqual(first.to_json(), second.to_json())

    def test_non_authorized_decision_carries_no_executable_authority(self):
        result = evaluate_governance(
            request(scope=("src/outside.py",)),
            grant(),
        )
        self.assertEqual(result.status, GovernanceStatus.BLOCKED)
        self.assertIsNone(result.authorized_scope)
        self.assertIsNone(result.permissions)
        self.assertIsNone(result.max_commands)
        self.assertIsNone(result.max_wall_time_seconds)
        self.assertIsNone(result.environment_ref)
        self.assertIsNone(result.acceptance_authority_ref)


class ContractIntegrityTests(unittest.TestCase):
    def test_request_requires_identity_and_explicit_scope(self):
        with self.assertRaises(ValueError):
            TaskRequest(
                request_id="",
                requester_ref="user://fixture",
                task_ref="task://fixture",
                project_ref="git://repo@base",
                requested_scope=("src/a.py",),
                required_permissions=(),
            )
        with self.assertRaises(ValueError):
            request(scope=())

    def test_invalid_budget_is_rejected_instead_of_coerced(self):
        for invalid in (0, -1, True):
            with self.subTest(max_commands=invalid):
                with self.assertRaises(ValueError):
                    grant(max_commands=invalid)
        for invalid in (0, -1, True, float("inf"), float("nan")):
            with self.subTest(max_wall_time_seconds=invalid):
                with self.assertRaises(ValueError):
                    grant(max_wall_time_seconds=invalid)

    def test_authority_requires_evidence(self):
        with self.assertRaises(ValueError):
            grant(evidence_refs=())
        with self.assertRaises(ValueError):
            grant(evidence_refs=("   ",))

    def test_unknown_is_distinct_from_explicit_empty_scope_and_permissions(self):
        scope_unknown = evaluate_governance(request(), grant(authorized_scope=None))
        scope_denied = evaluate_governance(request(), grant(authorized_scope=()))
        self.assertEqual(scope_unknown.status, GovernanceStatus.UNKNOWN)
        self.assertEqual(scope_denied.status, GovernanceStatus.BLOCKED)

        permission_unknown = evaluate_governance(request(), grant(permissions=None))
        permission_denied = evaluate_governance(request(), grant(permissions=()))
        self.assertEqual(permission_unknown.status, GovernanceStatus.UNKNOWN)
        self.assertEqual(permission_denied.status, GovernanceStatus.BLOCKED)

    def test_authorized_decision_cannot_omit_budget_or_acceptance_authority(self):
        with self.assertRaises(ValueError):
            GovernanceDecision(
                request_id="request",
                status=GovernanceStatus.AUTHORIZED,
                reasons=(GovernanceReason.AUTHORIZED,),
                grant_id="grant",
                authority_ref="authority",
                authorized_scope=("src/a.py",),
                permissions=("edit",),
                max_commands=None,
                max_wall_time_seconds=10,
                environment_ref="env://x",
                acceptance_authority_ref="acceptance://x",
                evidence_refs=("evidence://x",),
            )

    def test_non_authorized_decision_cannot_smuggle_execution_budget(self):
        with self.assertRaises(ValueError):
            GovernanceDecision(
                request_id="request",
                status=GovernanceStatus.BLOCKED,
                reasons=(GovernanceReason.SCOPE_DENIED,),
                max_commands=10,
            )

    def test_serialization_is_deterministic_and_executor_neutral(self):
        result = evaluate_governance(request(), grant())
        self.assertEqual(result.to_json(), result.to_json())
        payload = json.loads(result.to_json())
        self.assertEqual(payload["status"], "AUTHORIZED")
        self.assertNotIn("executor_id", payload)
        self.assertNotIn("adapter_id", payload)
        self.assertNotIn("route", payload)


if __name__ == "__main__":
    unittest.main()
