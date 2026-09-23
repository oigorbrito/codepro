import json
import unittest
from dataclasses import replace
from pathlib import Path

from arkx.characterization import RecommendedPath, Scope, TaskSignals, characterize
from arkx.contracts import ExecutionStatus
from arkx.progress import ProgressSnapshot, ProgressStatus, assess_progress
from arkx.routing import (
    BudgetState,
    EscalationAction,
    EvidenceSufficiency,
    ReasonCode,
    RoutingBudget,
    RoutingDecisionType,
    assess_escalation,
    route_characterization,
    CapabilityPolicyReason,
    assess_capability_policy,
)
from arkx.integration import AdapterIdentity, CapabilityProvenance, DependencyObservation, IntegrationKind, assess_preflight
from arkx.telemetry import TelemetryCollector


def characterization(scope: Scope):
    if scope is Scope.SIMPLE:
        signals = TaskSignals(
            candidate_files=("src/a.py",),
            dependency_edges=(),
            affected_components=("a",),
            known_tests=("test_a",),
            ambiguity_markers=(),
            risk_markers=(),
            acceptance_checks=("tests pass",),
        )
    elif scope is Scope.LOCALIZED:
        signals = TaskSignals(
            candidate_files=("src/a.py", "tests/test_a.py"),
            dependency_edges=(("a", "contracts"),),
            affected_components=("a",),
            known_tests=("test_a", "test_contracts"),
            ambiguity_markers=(),
            risk_markers=(),
            acceptance_checks=("tests pass", "round-trip pass"),
        )
    elif scope is Scope.REPOSITORY_WIDE:
        signals = TaskSignals(
            candidate_files=("a.py", "b.py", "c.py", "d.py", "e.py", "f.py"),
            dependency_edges=(("a", "b"), ("b", "c"), ("c", "shared"), ("tests", "a")),
            affected_components=("a", "b", "c"),
            known_tests=("test_a", "test_b", "test_c"),
            ambiguity_markers=(),
            risk_markers=(),
            acceptance_checks=("tests pass",),
            state_shared=True,
            architectural_change=True,
        )
    else:
        return characterize(TaskSignals())
    return characterize(signals)


def progress(status: ProgressStatus):
    base = ProgressSnapshot(
        useful_files=("src/a.py",),
        passing_tests=(),
        explained_failures=(),
        diff_distance=3,
        acceptance_distance=2,
        recent_actions=("run test_a",),
        failure_signatures=("failure-a",),
    )
    if status is ProgressStatus.PROGRESS_PROVEN:
        current = replace(base, passing_tests=("test_a",))
        return assess_progress(base, current)
    if status is ProgressStatus.NO_PROGRESS:
        return assess_progress(base, base)
    return assess_progress(None, ProgressSnapshot())


class RoutingTests(unittest.TestCase):
    def test_scopes_route_to_matching_paths(self):
        expected = {
            Scope.SIMPLE: RecommendedPath.SIMPLE_PATH,
            Scope.LOCALIZED: RecommendedPath.LOCALIZED_PATH,
            Scope.REPOSITORY_WIDE: RecommendedPath.REPOSITORY_WIDE_PATH,
        }
        for scope, path in expected.items():
            decision = route_characterization("task", characterization(scope))
            self.assertEqual(decision.decision, RoutingDecisionType.ROUTE)
            self.assertEqual(decision.selected_path, path)

    def test_unknown_characterization_requires_qualification(self):
        decision = route_characterization("task", characterization(Scope.UNKNOWN))
        self.assertEqual(decision.decision, RoutingDecisionType.REQUIRE_QUALIFICATION)
        self.assertEqual(decision.selected_path, RecommendedPath.QUALIFICATION_REQUIRED)

    def test_missing_characterization_requires_qualification(self):
        decision = route_characterization("task", None)
        self.assertEqual(decision.decision, RoutingDecisionType.REQUIRE_QUALIFICATION)

    def test_inconsistent_characterization_is_rejected(self):
        value = characterization(Scope.SIMPLE)
        invalid = replace(value, recommended_path=RecommendedPath.LOCALIZED_PATH)
        decision = route_characterization("task", invalid)
        self.assertEqual(decision.decision, RoutingDecisionType.REJECT_INVALID_INPUT)


class EscalationTests(unittest.TestCase):
    def test_simple_no_progress_escalates_to_localized(self):
        decision = assess_escalation(
            RecommendedPath.SIMPLE_PATH,
            progress(ProgressStatus.NO_PROGRESS),
            EvidenceSufficiency.INSUFFICIENT,
        )
        self.assertEqual(decision.action, EscalationAction.ESCALATE)
        self.assertEqual(decision.target_path, RecommendedPath.LOCALIZED_PATH)
        self.assertEqual(decision.budget_state.path_escalations_used, 1)

    def test_localized_no_progress_escalates_to_repository_wide(self):
        decision = assess_escalation(
            RecommendedPath.LOCALIZED_PATH,
            progress(ProgressStatus.NO_PROGRESS),
            EvidenceSufficiency.INSUFFICIENT,
        )
        self.assertEqual(decision.action, EscalationAction.ESCALATE)
        self.assertEqual(decision.target_path, RecommendedPath.REPOSITORY_WIDE_PATH)

    def test_repository_wide_stagnation_blocks(self):
        decision = assess_escalation(
            RecommendedPath.REPOSITORY_WIDE_PATH,
            progress(ProgressStatus.NO_PROGRESS),
            EvidenceSufficiency.INSUFFICIENT,
        )
        self.assertEqual(decision.action, EscalationAction.BLOCK)
        self.assertIn(ReasonCode.NO_HIGHER_PATH, decision.reason_codes)

    def test_progress_and_sufficient_evidence_stops_without_pass(self):
        decision = assess_escalation(
            RecommendedPath.SIMPLE_PATH,
            progress(ProgressStatus.PROGRESS_PROVEN),
            EvidenceSufficiency.SUFFICIENT,
        )
        self.assertEqual(decision.action, EscalationAction.STOP_SUFFICIENT_EVIDENCE)
        self.assertNotIn("PASS", decision.to_json())

    def test_progress_with_insufficient_evidence_continues_if_attempt_budget_exists(self):
        decision = assess_escalation(
            RecommendedPath.SIMPLE_PATH,
            progress(ProgressStatus.PROGRESS_PROVEN),
            EvidenceSufficiency.INSUFFICIENT,
        )
        self.assertEqual(decision.action, EscalationAction.CONTINUE)

    def test_unknown_evidence_cannot_stop(self):
        decision = assess_escalation(
            RecommendedPath.SIMPLE_PATH,
            progress(ProgressStatus.PROGRESS_PROVEN),
            EvidenceSufficiency.UNKNOWN,
        )
        self.assertEqual(decision.action, EscalationAction.REQUIRE_QUALIFICATION)

    def test_exhausted_budget_blocks(self):
        state = BudgetState(RoutingBudget(max_path_escalations=2, max_attempts=3), attempts_used=3, path_escalations_used=2)
        decision = assess_escalation(
            RecommendedPath.SIMPLE_PATH,
            progress(ProgressStatus.NO_PROGRESS),
            EvidenceSufficiency.INSUFFICIENT,
            budget_state=state,
        )
        self.assertEqual(decision.action, EscalationAction.BLOCK)

    def test_invalid_path_transition_blocks(self):
        decision = assess_escalation(
            RecommendedPath.QUALIFICATION_REQUIRED,
            progress(ProgressStatus.PROGRESS_PROVEN),
            EvidenceSufficiency.SUFFICIENT,
        )
        self.assertEqual(decision.action, EscalationAction.BLOCK)
        self.assertIn(ReasonCode.INVALID_PATH_TRANSITION, decision.reason_codes)


class DeterminismTests(unittest.TestCase):
    def test_same_inputs_have_byte_equivalent_routing_serialization(self):
        first = route_characterization("task", characterization(Scope.LOCALIZED))
        second = route_characterization("task", characterization(Scope.LOCALIZED))
        self.assertEqual(first.to_json(), second.to_json())

    def test_routing_decisions_do_not_change_p0_status(self):
        route_characterization("task", characterization(Scope.SIMPLE))
        execution = TelemetryCollector(task_id="task", run_id="run").summarize()
        self.assertEqual(execution.status, ExecutionStatus.NOT_EXECUTED)

    def test_synthetic_fixture_covers_seven_scenarios(self):
        path = Path(__file__).parents[1] / "experiments" / "routing-escalation-fixture.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["fixture_type"], "ROUTING_POLICY_FIXTURE")
        self.assertEqual(len(manifest["scenarios"]), 7)
        scopes = {scope.value: scope for scope in Scope}
        statuses = {status.value: status for status in ProgressStatus}
        sufficiencies = {value.value: value for value in EvidenceSufficiency}
        for scenario in manifest["scenarios"]:
            route = route_characterization("fixture", characterization(scopes[scenario["route_scope"]]))
            if "expected_route_decision" in scenario:
                self.assertEqual(route.decision.value, scenario["expected_route_decision"])
                continue
            self.assertEqual(route.selected_path.value, scenario["expected_path"])
            state = BudgetState(
                attempts_used=scenario.get("attempts_used", 0),
                path_escalations_used=scenario.get("path_escalations_used", 0),
            )
            decision = assess_escalation(
                route.selected_path,
                progress(statuses[scenario["progress"]]),
                sufficiencies[scenario["evidence"]],
                budget_state=state,
            )
            self.assertEqual(decision.action.value, scenario["expected_action"])
            if "expected_target" in scenario:
                self.assertEqual(decision.target_path.value, scenario["expected_target"])

class CapabilityRoutingTests(unittest.TestCase):
    def _preflight(self, provenance=CapabilityProvenance.OBSERVED, capabilities=("patch",)):
        return assess_preflight(
            AdapterIdentity(IntegrationKind.EXECUTOR, "executor", "1", "cfg"),
            (DependencyObservation("runtime", True, "1"),),
            capabilities=capabilities,
            capability_digest="capability-digest",
            capability_provenance=provenance,
        )

    def test_policy_requires_minimum_capability_provenance(self):
        decision = assess_capability_policy(self._preflight(), ("patch",), minimum_provenance=CapabilityProvenance.QUALIFIED)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, CapabilityPolicyReason.CAPABILITY_PROVENANCE_INSUFFICIENT)

    def test_policy_does_not_route_when_preflight_is_not_ready(self):
        preflight = assess_preflight(
            AdapterIdentity(IntegrationKind.EXECUTOR, "executor", "1", "cfg"),
            (DependencyObservation("runtime", False),),
            capabilities=("patch",), capability_digest="capability-digest",
            capability_provenance=CapabilityProvenance.OBSERVED,
        )
        decision = assess_capability_policy(preflight, ("patch",))
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, CapabilityPolicyReason.PREFLIGHT_NOT_READY)

    def test_policy_allows_observed_capability_when_required(self):
        decision = assess_capability_policy(self._preflight(), ("patch",), minimum_provenance=CapabilityProvenance.OBSERVED)
        self.assertTrue(decision.allowed)


if __name__ == "__main__":
    unittest.main()
