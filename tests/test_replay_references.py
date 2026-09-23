import unittest

from arkx.event_log import ReplayChain, classify_chain_references


class ReplayReferenceTests(unittest.TestCase):
    def test_reference_classification_preserves_missing_and_present(self):
        chain = ReplayChain(request_ref="request://1", execution_ref="execution://1")
        report = classify_chain_references(chain, available_refs={"request://1"})
        self.assertEqual(report.status(), "MISSING")
        self.assertEqual(report.present, ("request://1",))
        self.assertEqual(report.missing, ("execution://1",))

    def test_reference_classification_is_indeterminate_without_inventory(self):
        report = classify_chain_references(ReplayChain(request_ref="request://1"))
        self.assertEqual(report.status(), "INDETERMINATE")
        self.assertEqual(report.indeterminate, ("request://1",))


if __name__ == "__main__":
    unittest.main()
