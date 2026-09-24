import ast
import unittest
from pathlib import Path

from arkx.characterization import Scope, TaskSignals, characterize
from arkx.contracts import ExecutionStatus
from arkx.handoff import HandoffBudgetStatus, HandoffRecord, summarize_handoffs
from arkx.planning import RepositoryState, plan_repository
from arkx.progress import ProgressSnapshot, ProgressStatus, assess_progress
from arkx.routing import (
    EscalationAction,
    EvidenceSufficiency,
    RoutingDecisionType,
    assess_escalation,
    route_characterization,
)
from arkx.telemetry import TelemetryCollector
from arkx.verification import (
    PatchVerificationInput,
    PatchVerificationStatus,
    TestResult,
    TestResultStatus,
    verify_patch,
)


ROOT = Path(__file__).parents[1]
SRC = ROOT / "src" / "arkx"


def internal_import_graph() -> dict[str, set[str]]:
    modules = {
        path.stem
        for path in SRC.glob("*.py")
        if path.name != "__init__.py"
    }
    graph = {module: set() for module in modules}

    for path in SRC.glob("*.py"):
        if path.name == "__init__.py":
            continue
        source = path.stem
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            target = None
            if isinstance(node, ast.ImportFrom):
                if node.level and node.module:
                    target = node.module.split(".", 1)[0]
                elif node.module and node.module.startswith("arkx."):
                    target = node.module.split(".", 2)[1]
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("arkx."):
                        target = alias.name.split(".", 2)[1]
                        if target in modules and target != source:
                            graph[source].add(target)
            if target in modules and target != source:
                graph[source].add(target)
    return graph


def assert_acyclic(testcase: unittest.TestCase, graph: dict[str, set[str]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, trail: tuple[str, ...]) -> None:
        if node in visiting:
            testcase.fail("internal Arkx import cycle: " + " -> ".join(trail + (node,)))
        if node in visited:
            return
        visiting.add(node)
        for child in sorted(graph[node]):
            visit(child, trail + (node,))
        visiting.remove(node)
        visited.add(node)

    for node in sorted(graph):
        visit(node, ())


class ImportArchitectureTests(unittest.TestCase):
    def test_internal_module_graph_is_acyclic(self):
        graph = internal_import_graph()
        self.assertGreaterEqual(len(graph), 20)
        assert_acyclic(self, graph)


class VerticalCompositionTests(unittest.TestCase):
    def test_p1_through_p6_compose_without_execution_or_acceptance_leakage(self):
        characterization = characterize(
            TaskSignals(
                candidate_files=("src/a.py",),
                dependency_edges=(),
                affected_components=("a",),
                known_tests=("test_a",),
                ambiguity_markers=(),
                risk_markers=(),
                acceptance_checks=("tests pass",),
            )
        )
        self.assertEqual(characterization.scope, Scope.SIMPLE)

        route = route_characterization(
            "task-architecture",
            characterization,
            characterization_ref="characterization://task-architecture",
        )
        self.assertEqual(route.decision, RoutingDecisionType.ROUTE)

        previous = ProgressSnapshot(
            useful_files=("src/a.py",),
            passing_tests=(),
            explained_failures=(),
            diff_distance=2,
            acceptance_distance=1,
            recent_actions=("inspect src/a.py",),
            failure_signatures=("failure-a",),
        )
        current = ProgressSnapshot(
            useful_files=("src/a.py",),
            passing_tests=("test_a",),
            explained_failures=(),
            diff_distance=1,
            acceptance_distance=0,
            recent_actions=("run test_a",),
            failure_signatures=(),
        )
        progress = assess_progress(previous, current)
        self.assertEqual(progress.status, ProgressStatus.PROGRESS_PROVEN)

        escalation = assess_escalation(
            route.selected_path,
            progress,
            EvidenceSufficiency.SUFFICIENT,
        )
        self.assertEqual(escalation.action, EscalationAction.STOP_SUFFICIENT_EVIDENCE)

        plan = plan_repository(
            "repair a",
            RepositoryState(
                relevant_files=("src/a.py",),
                dependency_edges=(),
                impacted_components=("a",),
                affected_tests=("tests/test_a.py",),
                assumptions=(),
                unresolved_questions=(),
                completed_steps=(),
                remaining_steps=("inspect-01", "verify-affected-tests"),
            ),
        )
        self.assertGreaterEqual(len(plan.steps), 2)

        verification = verify_patch(
            PatchVerificationInput(
                task_id="task-architecture",
                issue_reproduction_required=True,
                issue_reproduced_before_patch=True,
                patch_applied=True,
                regression_results=(
                    TestResult(
                        "test_a",
                        TestResultStatus.PASSED,
                        True,
                        "evidence://test-a",
                    ),
                ),
                issue_reproduces_after_patch=False,
                changed_files=("src/a.py",),
                expected_scope=("src/a.py",),
                evidence_refs=("evidence://patch",),
            )
        )
        self.assertEqual(verification.status, PatchVerificationStatus.VERIFIED)

        handoff = summarize_handoffs(
            (
                HandoffRecord(
                    handoff_id="handoff-1",
                    source_executor="executor-a",
                    target_executor="executor-b",
                    reason="explicit synthetic composition fixture",
                    evidence_refs=("evidence://handoff",),
                    context_summary="bounded synthetic handoff",
                    context_bytes_in=10,
                    context_bytes_out=8,
                    duplicated_instructions=0,
                    duplicated_exploration=0,
                    discarded_context=2,
                    lost_information=(),
                ),
            )
        )
        self.assertEqual(handoff.budget_status, HandoffBudgetStatus.WITHIN_BUDGET)

        execution = TelemetryCollector(
            task_id="task-architecture",
            run_id="run-architecture",
        ).summarize()
        self.assertEqual(execution.status, ExecutionStatus.NOT_EXECUTED)

        serialized = "\n".join(
            (
                characterization.to_json(),
                route.to_json(),
                progress.to_json(),
                escalation.to_json(),
                plan.to_json(),
                verification.to_json(),
                handoff.to_json(),
            )
        )
        self.assertNotIn('"status":"PASS"', serialized)
        self.assertNotIn('"PROMOTED"', serialized)


class NormativeDocumentationTests(unittest.TestCase):
    def test_normative_docs_do_not_describe_pre_p1_bootstrap(self):
        project_contract = (ROOT / "docs" / "project-contract.md").read_text(encoding="utf-8")
        source_boundary = (ROOT / "src" / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("does not yet define routing, planning", project_contract)
        self.assertNotIn("No runtime implementation is part of the foundation bootstrap", source_boundary)

    def test_current_product_docs_use_codepro_identity(self):
        current_product_docs = (
            "docs/environment-manifest.md",
            "docs/experimental-protocol.md",
            "docs/protocol-deviation.md",
            "docs/study-spec.md",
            "docs/treatment-configuration.md",
            "docs/validity-plan.md",
        )
        for path in current_product_docs:
            with self.subTest(path=path):
                content = (ROOT / path).read_text(encoding="utf-8")
                self.assertNotIn("Arkx", content)
                self.assertNotIn("Dekon", content)


if __name__ == "__main__":
    unittest.main()
