import json
import unittest
from pathlib import Path

from arkx.planning import (
    PlanStep,
    ReplanRequest,
    ReplanTrigger,
    RepositoryState,
    StepStatus,
    build_plan,
    build_replan_result,
    plan_repository,
)


class PlanningTests(unittest.TestCase):
    def state(self):
        return RepositoryState(
            relevant_files=("src/b.py", "src/a.py"),
            dependency_edges=(("a", "b"),),
            impacted_components=("b", "a"),
            affected_tests=("tests/test_a.py",),
            assumptions=("dependency graph is explicit",),
            unresolved_questions=(),
            completed_steps=(),
            remaining_steps=("inspect a", "inspect b"),
        )

    def test_state_serialization_is_deterministic(self):
        first = self.state().to_json()
        second = RepositoryState(
            relevant_files=("src/a.py", "src/b.py"),
            dependency_edges=(("a", "b"),),
            impacted_components=("a", "b"),
            affected_tests=("tests/test_a.py",),
            assumptions=("dependency graph is explicit",),
            unresolved_questions=(),
            completed_steps=(),
            remaining_steps=("inspect b", "inspect a"),
        ).to_json()
        self.assertEqual(first, second)

    def test_state_cannot_mark_same_step_completed_and_remaining(self):
        with self.assertRaises(ValueError):
            RepositoryState(
                completed_steps=("same",),
                remaining_steps=("same",),
            )

    def test_plan_is_deterministic_and_does_not_complete_steps(self):
        plan = plan_repository("change components", self.state())
        self.assertEqual(
            plan.to_json(),
            plan_repository("change components", self.state()).to_json(),
        )
        self.assertTrue(all(step.status is StepStatus.PENDING for step in plan.steps))
        self.assertNotIn("PASS", plan.to_json())
        self.assertEqual(plan.schema_version, 2)

    def test_plan_creation_rejects_asserted_completion(self):
        with self.assertRaises(ValueError):
            build_plan(
                "goal",
                (PlanStep("a", "A", status=StepStatus.COMPLETED),),
                acceptance_criteria=("explicit outcome later",),
            )

    def test_plan_requires_acceptance_criteria(self):
        with self.assertRaises(ValueError):
            build_plan("goal", (PlanStep("a", "A"),))

    def test_dependency_order_is_preserved(self):
        plan = build_plan(
            "goal",
            (PlanStep("b", "B", depends_on=("a",)), PlanStep("a", "A")),
            acceptance_criteria=("verify goal",),
        )
        self.assertIn(["a", "b"], plan.to_dict()["dependencies"])

    def test_unknown_dependency_is_rejected(self):
        with self.assertRaises(ValueError):
            build_plan(
                "goal",
                (PlanStep("a", "A", depends_on=("missing",)),),
                acceptance_criteria=("verify goal",),
            )

    def test_cycle_is_rejected(self):
        with self.assertRaises(ValueError):
            build_plan(
                "goal",
                (
                    PlanStep("a", "A", depends_on=("b",)),
                    PlanStep("b", "B", depends_on=("a",)),
                ),
                acceptance_criteria=("verify goal",),
            )

    def test_replan_preserves_previous_plan_reference(self):
        plan = plan_repository("goal", self.state())
        request = ReplanRequest(
            ReplanTrigger.DEPENDENCY_DISCOVERED,
            "plan://old",
            ("evidence://1",),
            1,
        )
        result = build_replan_result(request, plan)
        self.assertEqual(result.to_dict()["previous_plan_ref"], "plan://old")

    def test_replan_requires_evidence(self):
        with self.assertRaises(ValueError):
            ReplanRequest(
                ReplanTrigger.DEPENDENCY_DISCOVERED,
                "plan://old",
                (),
                1,
            )

    def test_exhausted_replan_budget_cannot_create_new_plan_result(self):
        plan = plan_repository("goal", self.state())
        request = ReplanRequest(
            ReplanTrigger.BLOCKED_STEP,
            "plan://old",
            ("evidence://blocked",),
            0,
        )
        with self.assertRaises(ValueError):
            build_replan_result(request, plan)

    def test_fixture_is_classified_as_planning_fixture(self):
        path = Path(__file__).parents[1] / "experiments" / "repository-planning-fixture.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(value["fixture_type"], "REPOSITORY_PLANNING_FIXTURE")
        self.assertEqual(len(value["scenarios"]), 5)


if __name__ == "__main__":
    unittest.main()
