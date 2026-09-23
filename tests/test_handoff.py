import json
import unittest
from pathlib import Path

from arkx.handoff import HandoffBudgetStatus, HandoffPolicy, HandoffRecord, summarize_handoffs


def record(identifier="h1", **overrides):
    values = {
        "handoff_id": identifier,
        "source_executor": "a",
        "target_executor": "b",
        "reason": "capacity",
        "evidence_refs": ("e://handoff",),
        "context_summary": "summary",
        "context_bytes_in": 100,
        "context_bytes_out": 80,
        "duplicated_instructions": 1,
        "duplicated_exploration": 2,
        "discarded_context": 3,
        "lost_information": (),
    }
    values.update(overrides)
    return HandoffRecord(**values)


class HandoffTests(unittest.TestCase):
    def test_count_and_transition_are_deterministic(self):
        summary = summarize_handoffs((record(),))
        self.assertEqual(summary.handoffs, 1)
        self.assertEqual(summary.executor_transitions, (("a", "b"),))

    def test_context_bytes_and_duplicate_metrics_are_preserved(self):
        summary = summarize_handoffs((record(),))
        self.assertEqual(summary.context_bytes_in, 100)
        self.assertEqual(summary.context_bytes_out, 80)
        self.assertEqual(summary.duplicated_instructions, 1)
        self.assertEqual(summary.duplicated_exploration, 2)

    def test_unknown_measurements_are_not_zero(self):
        summary = summarize_handoffs((record(context_bytes_in=None, context_bytes_out=None),))
        self.assertIsNone(summary.context_bytes_in)
        self.assertIsNone(summary.context_bytes_out)

    def test_transitions_require_known_source_and_target(self):
        summary = summarize_handoffs((record(source_executor=None),))
        self.assertEqual(summary.executor_transitions, ())
        self.assertEqual(summary.budget_status, HandoffBudgetStatus.UNKNOWN)

    def test_lost_information_is_explicit(self):
        explicit = summarize_handoffs((record(lost_information=("constraint",)),))
        unknown = summarize_handoffs((record(lost_information=None),))
        self.assertEqual(explicit.lost_information_count, 1)
        self.assertIsNone(unknown.lost_information_count)

    def test_budget_exceeded_is_observable(self):
        summary = summarize_handoffs((record("h1"), record("h2"), record("h3")), HandoffPolicy(max_handoffs=2))
        self.assertEqual(summary.budget_status, HandoffBudgetStatus.BUDGET_EXCEEDED)

    def test_same_records_have_same_summary(self):
        first = summarize_handoffs((record(),)).to_json()
        second = summarize_handoffs((record(),)).to_json()
        self.assertEqual(first, second)

    def test_fixture_is_classified_as_handoff_fixture(self):
        path = Path(__file__).parents[1] / "experiments" / "handoff-accounting-fixture.json"
        value = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(value["fixture_type"], "HANDOFF_ACCOUNTING_FIXTURE")
        self.assertEqual(len(value["scenarios"]), 7)


if __name__ == "__main__":
    unittest.main()

