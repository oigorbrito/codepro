import unittest

from arkx.event_log import ChainIntegrity, ReferenceReport, ReplayChain, assess_chain_integrity


class ReplayIntegrityTests(unittest.TestCase):
    def test_chain_integrity_distinguishes_complete_incomplete_and_inconsistent(self):
        complete = ReplayChain("request", "plan", "execution", "verification", "acceptance", "promotion")
        self.assertEqual(assess_chain_integrity(complete, ReferenceReport(present=tuple(complete.to_dict().values()))), ChainIntegrity.COMPLETE)
        self.assertEqual(assess_chain_integrity(ReplayChain(request_ref="request"), ReferenceReport(indeterminate=("request",))), ChainIntegrity.INCOMPLETE)
        self.assertEqual(assess_chain_integrity(complete, ReferenceReport(missing=("promotion",))), ChainIntegrity.INCONSISTENT)


if __name__ == "__main__":
    unittest.main()
